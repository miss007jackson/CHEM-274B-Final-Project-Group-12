from banking_system import BankingSystem


class BankingSystemImpl(BankingSystem):
    def __init__(self):
        # account_id -> balance
        self.accounts: dict[str, int] = {}
        # account_id -> total outgoing amount (for ranking)
        self.outgoing: dict[str, int] = {}

        # To count ordinal number of withdrawals from all accounts
        self.payment_counter = 0
        # Dictionary to save account id, cashback amount, cashback time and status of cashback
        self.cashbacks = {}

    # ---------------------
    # Level 1 functionality
    # ---------------------

    def create_account(self, timestamp: int, account_id: str) -> bool:
        # Create only if it doesn't exist
        if account_id in self.accounts:
            return False
        self.accounts[account_id] = 0
        self.outgoing[account_id] = 0
        return True

    def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None:
        self.process_cashbacks(timestamp)

        # Deposit only into an existing account
        if account_id not in self.accounts:
            return None
        self.accounts[account_id] += amount
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
        return self.accounts[source_account_id]

    # ---------------------
    # Level 2 functionality
    # ---------------------

    def top_spenders(self, timestamp: int, n: int) -> list[str]:
        self.process_cashbacks(timestamp)

        # Prepare sortable list of (account_id, total_outgoing)
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

    # Adding a helper function for cashback status
    def process_cashbacks(self, timestamp: int):
        for id, info in self.cashbacks.items():
            if info["status"] == "IN_PROGRESS" and timestamp >= info["cashback_time"]:
                # Process cashback
                info["status"] = "CASHBACK_RECEIVED"
                self.accounts[info["account_id"]] += info["cashback_amount"]

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

        self.payment_counter += 1
        payment_id = f"payment{self.payment_counter}"

        # Calculate cashback (2% of amount, rounded to nearest integer)
        cashback_amount = (amount * 2) // 100
        cashback_time = (
            timestamp + 86400000
        )  # waiting period: 24 hours (24*60*60*1000 ms)

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

        # Validate account
        if account_id not in self.accounts:
            return None
        # Validate payment
        if payment not in self.cashbacks:
            return None
        cashback_info = self.cashbacks[payment]
        # Validate account matches payment
        if cashback_info["account_id"] != account_id:
            return None

        return cashback_info["status"]
