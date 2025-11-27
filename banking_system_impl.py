from banking_system import BankingSystem


class BankingSystemImpl(BankingSystem):
    def __init__(self):
        # account_id -> balance
        self.accounts: dict[str, int] = {}
        # account_id -> total outgoing amount (for ranking)
        self.outgoing: dict[str, int] = {}

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

    # ----------------------
    # Level 2 functionality
    # ----------------------

    def top_spenders(self, timestamp: int, n: int) -> list[str]:
        # Prepare sortable list of (account_id, total_outgoing)
        entries = [
            (acc_id, self.outgoing.get(acc_id, 0)) for acc_id in self.accounts.keys()
        ]
        # Sort by (-total_outgoing, account_id)
        entries.sort(key=lambda x: (-x[1], x[0]))
        # Take up to n and format
        result = [f"{acc_id}({total})" for acc_id, total in entries[:n]]
        return result
