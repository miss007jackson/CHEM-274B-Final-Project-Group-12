# Level 4 Code


from banking_system import BankingSystem


MILLISECONDS_IN_1_DAY = 24 * 60 * 60 * 1000


class BankingSystemImpl(BankingSystem):
    def __init__(self):
        # account_id -> current balance (only for *active* accounts, not merged-away ones)
        self.accounts: dict[str, int] = {}
        # account_id -> total outgoing amount (for ranking)
        self.outgoing: dict[str, int] = {}

        # To count ordinal number of withdrawals from all accounts
        self.payment_counter = 0
        # payment_id -> {account_id, cashback_amount, cashback_time, status}
        self.cashbacks: dict[str, dict] = {}
        # a dict of dicts

        # -------- Level 4 bookkeeping --------
        # account_id -> list of (timestamp, balance_after_that_timestamp)
        self.balance_history: dict[str, list[tuple[int, int]]] = {}
        # account_id -> creation timestamp
        self.created_at: dict[str, int] = {}
        # account_id -> merge timestamp (when this account was merged INTO another one)
        self.merge_time: dict[str, int] = {}

    # ---------------------
    # Helper methods
    # ---------------------

    def _record_balance(self, account_id: str, timestamp: int):
        """Record the balance of account_id at the given timestamp."""
        if account_id not in self.balance_history:
            self.balance_history[account_id] = []
        # We assume we call this in non-decreasing timestamp order per account
        self.balance_history[account_id].append((timestamp, self.accounts[account_id]))

    def _get_balance_at_time(self, account_id: str, time_at: int) -> int | None:
        """Return balance of account_id at time_at, or None if it didn't exist then."""
        # Must have been created
        created = self.created_at.get(account_id)
        if created is None or time_at < created:
            return None

        # If account was merged away, it ceases to exist at merge_time and later
        mt = self.merge_time.get(account_id)
        if mt is not None and time_at >= mt:
            return None

        history = self.balance_history.get(account_id, [])
        last_balance: int | None = None
        for ts, bal in history:
            if ts <= time_at:
                last_balance = bal
            else:
                break
        return last_balance

    # ---------------------
    # Level 3 helper: cashback processing
    # ---------------------

    def process_cashbacks(self, timestamp: int):
        """
        Process all due cashbacks as of 'timestamp'.
        Cashback is effectively applied at 'cashback_time' (not 'timestamp'),
        so we record history with that earlier timestamp.
        """
        for pid, info in self.cashbacks.items():
            if info["status"] == "IN_PROGRESS" and timestamp >= info["cashback_time"]:
                info["status"] = "CASHBACK_RECEIVED"
                acc_id = info["account_id"]
                # acc_id should still be an active account (possibly after merge)
                if acc_id in self.accounts:
                    self.accounts[acc_id] += info["cashback_amount"]
                    # record balance at the cashback time
                    self._record_balance(acc_id, info["cashback_time"])

    # ---------------------
    # Level -1 functionality
    # ---------------------

    def create_account(self, timestamp: int, account_id: str) -> bool:
        # If currently active, cannot create
        if account_id in self.accounts:
            return False

        # Re-create allowed: reset lifecycle state
        self.accounts[account_id] = 0
        self.outgoing[account_id] = 0
        self.created_at[account_id] = timestamp
        # Clear previous merge_time (if any) to mark it active again
        if account_id in self.merge_time:
            del self.merge_time[account_id]
        # Start a fresh balance history for this lifecycle
        self.balance_history[account_id] = []
        self._record_balance(account_id, timestamp)

        return True

    def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None:
        self.process_cashbacks(timestamp)

        if account_id not in self.accounts:
            return None
        self.accounts[account_id] += amount
        self._record_balance(account_id, timestamp)
        return self.accounts[account_id]

    def transfer(
        self,
        timestamp: int,
        source_account_id: str,
        target_account_id: str,
        amount: int,
    ) -> int | None:

        self.process_cashbacks(timestamp)

        # Validate accounts and different IDs
        if (
            source_account_id not in self.accounts
            or target_account_id not in self.accounts
            or source_account_id == target_account_id
        ):
            return None
        # Validate sufficient funds
        if self.accounts[source_account_id] < amount:
            return None

        # Perform transfer
        self.accounts[source_account_id] -= amount
        self.accounts[target_account_id] += amount

        # Track outgoing for source (successful transfer only)
        self.outgoing[source_account_id] += amount

        # Record balances for both accounts at this timestamp
        self._record_balance(source_account_id, timestamp)
        self._record_balance(target_account_id, timestamp)

        return self.accounts[source_account_id]

    # ---------------------
    # Level -2 functionality
    # ---------------------

    def top_spenders(self, timestamp: int, n: int) -> list[str]:
        self.process_cashbacks(timestamp)

        # Only active accounts matter for ranking
        entries = [
            (acc_id, self.outgoing.get(acc_id, 0)) for acc_id in self.accounts.keys()
        ]
        # Sort by (-total_outgoing, account_id)
        entries.sort(key=lambda x: (-x[1], x[0]))
        # Take up to n and format
        result = [f"{acc_id}({total})" for acc_id, total in entries[:n]]
        return result

    # ---------------------
    # Level 3 functionality
    # ---------------------

    def pay(self, timestamp: int, account_id: str, amount: int) -> str | None:
        self.process_cashbacks(timestamp)

        # Validate account:
        if account_id not in self.accounts:
            return None
        # Validate sufficient funds
        if self.accounts[account_id] < amount:
            return None

        # Payment made
        self.accounts[account_id] -= amount
        # Track outgoing
        self.outgoing[account_id] += amount
        # Record balance after withdrawal
        self._record_balance(account_id, timestamp)

        self.payment_counter += 1
        payment_id = f"payment{self.payment_counter}"

        # Calculate cashback (2% of amount, rounded down)
        cashback_amount = (amount * 2) // 100
        cashback_time = timestamp + MILLISECONDS_IN_1_DAY

        # Store cashback info
        self.cashbacks[payment_id] = {
            "account_id": account_id,
            "cashback_amount": cashback_amount,
            "cashback_time": cashback_time,
            "status": "IN_PROGRESS",
        }

        return payment_id

    def get_payment_status(
        self, timestamp: int, account_id: str, payment: str
    ) -> str | None:
        self.process_cashbacks(timestamp)

        # For this method, "account exists" means it's currently active
        # (after a merge, you must use the surviving account_id).
        if account_id not in self.accounts:
            return None
        if payment not in self.cashbacks:
            return None

        cashback_info = self.cashbacks[payment]
        # Validate account matches payment
        if cashback_info["account_id"] != account_id:
            return None

        return cashback_info["status"]

    # ---------------------
    # Level -4 functionality
    # ---------------------

    def merge_accounts(
        self, timestamp: int, account_id_1: str, account_id_2: str
    ) -> bool:

        self.process_cashbacks(timestamp)

        # Invalid if equal or either doesn't exist
        if account_id_1 == account_id_2:
            return False
        if account_id_1 not in self.accounts or account_id_2 not in self.accounts:
            return False

        # 1) Add balances
        self.accounts[account_id_1] += self.accounts[account_id_2]

        # 2) Merge outgoing totals
        self.outgoing[account_id_1] += self.outgoing.get(account_id_2, 0)

        # 3) Redirect pending cashbacks from account_id_2 to account_id_1
        for info in self.cashbacks.values():
            if info["status"] == "IN_PROGRESS" and info["account_id"] == account_id_2:
                info["account_id"] = account_id_1

        # 4) Mark account_id_2 as merged at this timestamp
        self.merge_time[account_id_2] = timestamp

        # 5) Remove account_id_2 from active structures
        if account_id_2 in self.accounts:
            del self.accounts[account_id_2]
        if account_id_2 in self.outgoing:
            del self.outgoing[account_id_2]

        # 6) Record new balance for account_id_1 at this timestamp
        self._record_balance(account_id_1, timestamp)

        return True

    def get_balance(self, timestamp: int, account_id: str, time_at: int) -> int | None:
        """
        Return the balance of 'account_id' at logical time 'time_at'.
        - If the account did not exist at time_at, return None.
        - If time_at is after the account was merged away, return None.
        - If queries ran at time_at, we treat the balance *after* those queries.
        """
        self.process_cashbacks(timestamp)

        # If account was never created, no balance history
        if account_id not in self.created_at:
            return None

        return self._get_balance_at_time(account_id, time_at)
