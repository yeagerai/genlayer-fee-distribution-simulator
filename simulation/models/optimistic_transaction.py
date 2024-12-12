# simulation/models/optimistic_transaction.py


from simulation.utils import generate_ethereum_address
from simulation.models.transaction_budget import TransactionBudget
from simulation.models.round import Round
from simulation.models.enums import Role, Vote
from simulation.models.participant import Participant


class OptTransaction:
    def __init__(
        self,
        transaction_budget: TransactionBudget,
        initial_validator_pool: dict[str],
    ):
        self.id = generate_ethereum_address()
        self.transaction_budget = transaction_budget
        self.initial_validator_pool = initial_validator_pool

        self.rounds = []
        self.final = False

    def start(self, leader_result, voting_vector):
        """Initialize first round of the transaction"""
        first_round = Round(
            round_number=1,
            leader_fee_units=self.initial_leader_budget,
            validator_fee_units=self.initial_validator_budget,
            leader_result=leader_result,
            voting_vector=voting_vector,  # Will be set when votes are received
            previous_rounds=None,
        )
        self.rounds.append(first_round)
        return first_round

    def add_new_round(self, leader_result, voting_vector):
        """Add a new round after appeal/rotation"""
        if self.final:
            return None

        if len(voting_vector) != 2 * len(self.rounds[-1].voting_vector) + 1:
            return IndexError()

        new_round = Round(
            round_number=len(self.rounds) + 1,
            leader_fee_units=self.initial_leader_budget,
            validator_fee_units=self.initial_validator_budget,
            leader_result=leader_result,
            voting_vector=voting_vector,
            previous_rounds=self.rounds,
        )
        self.rounds.append(new_round)
        return new_round

    def print_current_rewards(self):
        for r in self.rounds:
            print("Round: {r.id}")
            for p in self.initial_validator_pool:
                if p.rewards[r.id]:  # or not KeyError
                    print("\t{p.id} got: {p.rewards[r.id]}")


def main():
    # Initialize validator pool
    initial_validators_pool = [Participant() for _ in range(1000)]

    # Initialize validator pool
    appealants_pool = [Participant(role=Role.APPEALANT) for _ in range(10)]

    num_messages_per_preset = {
        "0x..._m1": 1,
        "0x..._m2": 3,
        "default": 1,
        "deploy": 1,
    }

    # Create transaction budget
    tx_budget = TransactionBudget(
        initial_leader_budget=50,
        initial_validator_budget=60,
        rotation_budget=[20, 20, 20, 20, 20, 20, 20],
        appeal_rounds_budget=[30, 30, 30, 30, 30, 30, 30],
        total_internal_messages_budget=1000,
    )

    # Create and run transaction
    new_tx = OptTransaction(tx_budget, initial_validators_pool)

    # Simulate first round
    new_tx.start([Vote.AGREE, Vote.DISAGREE, Vote.AGREE, Vote.AGREE, Vote.DISAGREE])
    new_tx.print_current_rewards()

    # Simulate appeal
    new_tx.rounds[-1].appeal(
        [
            Vote.AGREE,
            Vote.AGREE,
            Vote.DISAGREE,
            Vote.AGREE,
            Vote.DISAGREE,
        ]
    )
    new_tx.print_current_rewards()

    # Add new round
    new_tx.add_new_round(
        [
            Vote.DISAGREE,
            Vote.DISAGREE,
            Vote.AGREE,
            Vote.DISAGREE,
            Vote.AGREE,
        ]
    )
    new_tx.print_current_rewards()

    # Simulate another appeal
    new_tx.rounds[-1].appeal(
        [
            Vote.DISAGREE,
            Vote.AGREE,
            Vote.DISAGREE,
            Vote.AGREE,
            Vote.AGREE,
        ]
    )
    new_tx.print_current_rewards()

    # Add another new round
    new_tx.add_new_round(
        [
            Vote.AGREE,
            Vote.AGREE,
            Vote.DISAGREE,
            Vote.AGREE,
            Vote.DISAGREE,
        ]
    )
    new_tx.print_current_rewards()


if __name__ == "__main__":
    main()
