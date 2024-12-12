# simulation/models/round.py

from datetime import datetime

from simulation.config_constants import FINALITY_WINDOW_MINS
from simulation.models.appeal import Appeal
from simulation.models.enums import Vote, AppealType, LeaderResult
from simulation.utils import generate_ethereum_address
from simulation.models.participant import Participant
from simulation.models.transaction_budget import TransactionBudget


class Round:
    def __init__(
        self,
        round_number: int,
        transaction_budget: TransactionBudget,
        initial_validator_pool: dict[str, Participant] | None = None,
        leader_result: LeaderResult | None = None,
        voting_vector: list[Vote] | None = None,
        messages_per_preset: dict[str, int] = {},
        previous_rounds: list["Round"] | None = None,
    ):
        self.id = generate_ethereum_address()
        self.round_number = round_number
        self.transaction_budget = transaction_budget
        self.previous_rounds = previous_rounds
        self.messages_per_preset = messages_per_preset
        self.voting_vector = voting_vector
        self.appeals = []

        self.leader, self.validators = self.validators_and_leader_selection()
        self.calculate_majority()
        self.distribute_rewards()

        automatic_next_step = self.compute_automatic_next_step()
        if automatic_next_step:
            # either deterministic_violation_appeal + rotation
            # or rotation
            ...
        else:
            self.start_finality_window = datetime.now()

    def validators_and_leader_selection(self) -> tuple[Participant, list[Participant]]:
        leader = ...
        selected_validators = ...
        return leader, selected_validators

    def compute_automatic_next_step(
        self,
    ): ...  # TODO: either detemrinistic_violation_appeal or rotation based on majority and budget

    def calculate_majority(self):
        vote_counts = {"A": 0, "D": 0, "T": 0, "I": 0, "V": 0}
        for vote in self.voting_vector:
            vote_counts[vote] += 1

        total_votes = len(self.voting_vector)
        majority_threshold = (total_votes // 2) + 1

        if vote_counts["A"] >= majority_threshold:
            self.majority = "A"
        elif vote_counts["T"] >= majority_threshold:
            self.majority = "T"
        elif vote_counts["V"] >= majority_threshold:
            self.majority = "V"
        elif vote_counts["D"] >= majority_threshold:
            # As they disagree but they don't agree on anything in particular
            self.majority = None
        else:
            self.majority = None  # No clear majority

    def distribute_rewards(self):
        """
        TODO:
        - leader pone el receipt -> (inital_leader_budget)
            - if leader timeout -> 50%
            - if leader idle -> 0 + slashing (1% del stake config variable)

        - vals:
            - si hay alguno IDLE => slash + un tio nuevo a la ronda
                - si hay mayoría -> (equal split entre la mayoría, el resto 0)
                - si no hay mayoría -> (equal split)
        hay que hacer rotate?
            SI y hay budget:
                - leader out, new leader in
                - se le quita el budget al leader antiguo (if next round not undetermined)
                - se empieza newRound
                EX:
                    (U,U,A)
                        -> new leader, de quien coge el dinero? sobra dinero que va al user
        """

    def start_appeal(
        self, appeal_type: AppealType, bond: int, voting_vector: list[Vote] | None
    ):
        if datetime.now() < self.start_finality_window + FINALITY_WINDOW_MINS * 60:
            # starts the appeal round
            self.appeals.append(Appeal(appeal_type, bond, voting_vector))
            ...  # handle different appeal types
            self.appeals[-1].distribute_rewards()
        else:
            return TimeoutError("Can't appeal after finality window finishes")
