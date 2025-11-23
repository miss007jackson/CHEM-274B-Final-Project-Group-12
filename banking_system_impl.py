from banking_system import BankingSystem


class BankingSystemImpl(BankingSystem):

    def __init__(self):
        # account_id -> balance
        self.accounts: dict[str, int] = {}

    # Level 1

    def create_account(self, timestamp: int, account_id: str) -> bool:
        if account_id in self.accounts:
            return False
        self.accounts[account_id] = 0
        return True

    def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None:
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
        # Validate accounts exist and are different
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
        return self.accounts[source_account_id]
