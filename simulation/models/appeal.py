# simulation/models/appeal.py

from simulation.utils import generate_ethereum_address
from simulation.models.enums import AppealType
from simulation.models.participant import Participant


class Appeal:
    def __init__(
        self,
        appeal_type: AppealType,
        bond: int,
        voting_vector: list[str] | None = None,
    ):
        self.id = generate_ethereum_address()
        self.bond = bond
        self.voting_vector = voting_vector
        self.participants: list[Participant] = (
            ...
        )  # always pull more vals but depends on appeal type how those are pulled
        self.successful = None
        self.appealant_reward = 0
        if appeal_type == AppealType.LEADER:
            self.reward_modifier = 1.5
        elif appeal_type == AppealType.VALIDATOR:
            self.reward_modifier = 1.2
        else:
            self.reward_modifier = 0  # TRIBUNAL

        self.execute()

    def calculate_result(self):
        """Calculate if appeal was successful based on voting vector"""
        if not self.voting_vector:
            return False

        agree_votes = self.voting_vector.count("A")
        total_votes = len(self.voting_vector)
        return agree_votes > total_votes // 2

    def execute(self):
        self.successful = self.calculate_result()
        if self.successful:
            self.appealant_reward = self.bond * self.reward_modifier

    def distribute_rewards(self):
        """
        TODO:
        if under finality_window:
            - leader_appeal:
                - newRound 2N+1
                    - if voting vector majority != prev Round
                    - successful:
                        appealant -> old leader + bond
                        old vals + el user paga el resto del budget, sino top up transaction
                    - no successful:
                        - user pays round from budget
                        - appealant bond -> splits equally / 2*N+1
            - val_appeal:
                appealant bond -> new vals pulled gas
                - si no es successful:
                    - new vals that are on winning majority -> bond equal split

                - si es successful (new majority type):
                    - old leader + bond -> appealant
                    - old validators (prev majority) -> new winning majority type
                    - newRound (if no budget, no appeal) (DEV LINX)

            - tribunal transaction:
                val_appeal (no bond + no rewards)
                final
        """
