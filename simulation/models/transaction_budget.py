# simulation/transaction_budget.py


from typing import Optional


class PresetLeaf:
    def __init__(
        self,
        initial_leader_budget: int = 0,
        initial_validator_budget: int = 0,
        rotation_budget: list[int] = [0, 0, 0, 0, 0, 0, 0],
        appeal_rounds_budget: list[int] = [0, 0, 0, 0, 0, 0, 0],
    ):
        self.initial_leader_budget = initial_leader_budget
        self.initial_validator_budget = initial_validator_budget
        self.rotation_budget = rotation_budget
        self.appeal_rounds_budget = appeal_rounds_budget

    def compute_total_gas(self) -> int:
        return (
            self.initial_leader_budget
            + self.initial_validator_budget
            + sum(self.rotation_budget)
            + sum(self.appeal_rounds_budget)
        )


class PresetBranch:
    def __init__(
        self,
        initial_leader_budget: int = 0,
        initial_validator_budget: int = 0,
        rotation_budget: list[int] = [0, 0, 0, 0, 0, 0, 0],
        appeal_rounds_budget: list[int] = [0, 0, 0, 0, 0, 0, 0],
        internal_messages_budget_guess: dict[
            str, str
        ] = {},  # message_key -> reference_key mapping
        external_messages_budget_guess: list[int] = [],
    ):
        self.initial_leader_budget = initial_leader_budget
        self.initial_validator_budget = initial_validator_budget
        self.rotation_budget = rotation_budget
        self.appeal_rounds_budget = appeal_rounds_budget
        self.internal_messages_budget_guess = internal_messages_budget_guess
        self.external_messages_budget_guess = external_messages_budget_guess

    def compute_own_gas(self) -> int:
        return (
            self.initial_leader_budget
            + self.initial_validator_budget
            + sum(self.rotation_budget)
            + sum(self.appeal_rounds_budget)
            + sum(self.external_messages_budget_guess)
        )


class TransactionBudget:
    def __init__(
        self,
        initial_leader_budget: int = 0,
        initial_validator_budget: int = 0,
        rotation_budget: list[int] = [0, 0, 0, 0, 0, 0, 0],
        appeal_rounds_budget: list[int] = [0, 0, 0, 0, 0, 0, 0],
        preset_leafs: dict[str, PresetLeaf] = {},
        preset_branches: dict[str, PresetBranch] = {},
        total_internal_messages_budget: int = 0,
        external_messages_budget_guess: list[int] = [],
    ):
        self.initial_leader_budget = initial_leader_budget
        self.initial_validator_budget = initial_validator_budget
        self.rotation_budget = rotation_budget
        self.appeal_rounds_budget = appeal_rounds_budget
        self.preset_leafs = preset_leafs
        self.preset_branches = preset_branches
        self.total_internal_messages_budget = total_internal_messages_budget
        self.external_messages_budget_guess = external_messages_budget_guess
        self.remaining_gas = total_internal_messages_budget

    def compute_internal_message_budget(self, message_key: str) -> Optional[int]:
        """
        Compute gas cost for a specific message by recursively following branch->branch->leaf references
        """
        # First check if it's a leaf
        if message_key in self.preset_leafs:
            leaf = self.preset_leafs[message_key]
            gas = leaf.compute_total_gas()

            if gas > self.remaining_gas:
                return None

            self.remaining_gas -= gas
            return gas

        # Then check if it's a branch
        if message_key in self.preset_branches:
            branch = self.preset_branches[message_key]
            total_gas = branch.compute_own_gas()

            # Add gas from referenced messages (could be branches or leaves)
            for referenced_key in branch.internal_messages_budget_guess.values():
                # Recursively compute gas for each referenced message
                referenced_gas = self.compute_internal_message_budget(referenced_key)
                if referenced_gas is None:
                    return None  # Invalid reference or out of gas

                total_gas += referenced_gas

            if total_gas > self.remaining_gas:
                return None

            self.remaining_gas -= total_gas
            return total_gas

        return None  # Key not found


def main():
    # Create some leaf nodes
    leaf1 = PresetLeaf(10, 20, [1, 2, 3], [4, 5, 6])
    leaf2 = PresetLeaf(5, 15, [1, 1, 1], [2, 2, 2])

    # Create nested branches
    branch2 = PresetBranch(5, 15, [1, 1, 1], [2, 2, 2], {"0x...m6": "l1"})
    branch1 = PresetBranch(
        5,
        15,
        [1, 1, 1],
        [2, 2, 2],
        {"0x...m5": "l2", "0x...m4": "0x..._m3"},  # References another branch
    )

    # Create transaction budget
    tx = TransactionBudget(
        initial_leader_budget=100,
        initial_validator_budget=200,
        preset_leafs={"l1": leaf1, "l2": leaf2},
        preset_branches={"0x..._m3": branch2, "0x..._m7": branch1},
        total_internal_messages_budget=1000,
    )

    # Compute gas for a specific message
    total_gas = tx.compute_internal_message_budget("0x..._m7")
    assert total_gas == 138
    print(f"Total gas for message: {total_gas}")


if __name__ == "__main__":
    main()
