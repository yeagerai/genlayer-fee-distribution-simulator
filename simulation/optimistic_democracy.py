# simulation/transaction_simulator.py

from simulation.constants import (
    VOTE_AGREE,
    VOTE_DISAGREE,
    VOTE_IDLE,
    VOTE_TIMEOUT,
    VOTE_VIOLATION,
)
from simulation.utils import generate_mermaid_flowchart
from simulation.validator_selection import select_validators, initialize_validators_list
from simulation.models import Validator
from simulation.fee_mechanism import distribute_fees


class TransactionSimulator:
    def __init__(
        self,
        all_validators,
        r,
        leader_decision,
        appeal,
        fee_structure,
        validators_list=None,
    ):
        self.all_validators = all_validators
        self.r = r
        self.leader_decision = leader_decision
        self.appeal = appeal
        self.fee_structure = fee_structure
        self.transaction_path = []
        self.retry_count = 0
        self.leader_index = 0
        self.validators_list = validators_list if validators_list else []
        self.leader = None
        self.validators = []
        self.N_r = 0
        self.tau_r = 0
        self.total_validators_available = len(all_validators)
        self.max_retries = 0

    def run_simulation(self):
        """Main method to run the transaction simulation."""
        self.initialize_validators()
        self.update_majority_threshold()
        self.max_retries = min(len(self.validators_list), 10)

        while True:
            self.setup_leader_and_validators()
            votes, votes_counts = self.execute_round()
            blocking_scenario = self.detect_blocking_scenario(votes_counts)

            if blocking_scenario:
                continue_simulation = self.handle_blocking_scenario(blocking_scenario)
                if not continue_simulation:
                    break
            else:
                self.transaction_path.append(
                    "No blocking scenario detected. Transaction proceeds."
                )
                self.distribute_rewards_and_penalties()
                break  # Transaction successful

        self.output_results()

    def initialize_validators(self):
        """Initializes the initial set of validators."""
        if not self.validators_list:
            initial_validator_count = 2 ** (self.r + 2) + 1
            selected_validators = select_validators(
                initial_validator_count, self.all_validators
            )
            self.validators_list = [
                Validator(id=val[0], stake=val[1]) for val in selected_validators
            ]
        self.N_r = len(self.validators_list)

    def update_majority_threshold(self):
        """Updates the majority threshold τr based on current validator count."""
        self.tau_r = (self.N_r + 1) // 2

    def setup_leader_and_validators(self):
        """Sets up the leader and validators for the current round."""
        self.leader, self.validators = initialize_validators_list(
            self.validators_list, self.leader_decision
        )
        self.transaction_path.append(f"Round {self.retry_count + 1}")
        self.transaction_path.append(f"Leader's vote: {self.leader.decision}")

    def execute_round(self):
        """Executes a single round of voting."""
        votes, votes_counts = self.collect_votes()
        self.record_votes(votes, votes_counts)
        return votes, votes_counts

    def collect_votes(self):
        """Collect votes from the leader and validators."""
        votes = []
        votes_counts = {
            VOTE_AGREE: 0,
            VOTE_DISAGREE: 0,
            VOTE_TIMEOUT: 0,
            VOTE_IDLE: 0,
            VOTE_VIOLATION: 0,
        }

        # Leader's vote
        leader_vote = self.leader.decision
        votes.append(leader_vote)
        votes_counts[leader_vote] += 1

        # Validators' votes
        for validator in self.validators:
            vote = validator.vote()
            votes.append(vote)
            votes_counts[vote] += 1

        return votes, votes_counts

    def record_votes(self, votes, votes_counts):
        """Records the votes into the transaction path."""
        validator_votes = [
            f"{vote} (Validator {validator.id})"
            for validator, vote in zip(self.validators, votes[1:])
        ]
        self.transaction_path.append(f"Validator votes: {', '.join(validator_votes)}")
        self.transaction_path.append(
            f"Vote counts: A={votes_counts[VOTE_AGREE]}, D={votes_counts[VOTE_DISAGREE]}, "
            f"T={votes_counts[VOTE_TIMEOUT]}, I={votes_counts[VOTE_IDLE]}, V={votes_counts[VOTE_VIOLATION]}"
        )
        self.transaction_path.append(f"Total validators Nr: {self.N_r}")
        self.transaction_path.append(f"Majority threshold τr: {self.tau_r}")

    def detect_blocking_scenario(self, votes_counts):
        """Detects if there is a blocking scenario based on the votes."""
        leader_vote = self.leader.decision
        X_r = votes_counts[VOTE_AGREE]
        Y_r = votes_counts[VOTE_DISAGREE]
        Z_r = votes_counts[VOTE_TIMEOUT]
        V_r = votes_counts[VOTE_IDLE]
        W_r = votes_counts[VOTE_VIOLATION]

        blocking_scenario = None
        if leader_vote == VOTE_IDLE:
            blocking_scenario = "Leader IDLE (LI)"
        elif leader_vote == VOTE_TIMEOUT:
            blocking_scenario = "Leader times out (LT)"
        elif W_r >= 1:
            blocking_scenario = "Deterministic Violation (DV)"
        elif V_r >= self.tau_r or V_r == self.N_r:
            blocking_scenario = "IDLE exceeds (IE)"
        elif Z_r >= self.tau_r or Z_r == self.N_r:
            blocking_scenario = "Timeout exceeds (TE)"
        elif (X_r) == Y_r:
            blocking_scenario = "Agrees equal disagrees (AED)"
        elif (X_r) < self.tau_r:
            blocking_scenario = "Insufficient Agree Votes (IA)"
        elif Y_r > self.N_r - self.tau_r + 1:
            blocking_scenario = "Excessive Disagree Votes (ED)"

        if blocking_scenario:
            self.transaction_path.append(
                f"Blocking scenario detected: {blocking_scenario}"
            )
        return blocking_scenario

    def handle_blocking_scenario(self, blocking_scenario):
        """Handles blocking scenarios and decides whether to continue the simulation."""
        if blocking_scenario in ["Leader IDLE (LI)", "Leader times out (LT)"]:
            return self.process_leader_failure(blocking_scenario)
        elif blocking_scenario == "Deterministic Violation (DV)":
            self.penalize_violating_validators(VOTE_VIOLATION)
            self.transaction_path.append("Transaction failed due to violation.")
            return False
        elif blocking_scenario == "IDLE exceeds (IE)":
            self.penalize_violating_validators(VOTE_IDLE)
            self.transaction_path.append(
                "Transaction failed due to excessive idle validators."
            )
            return False
        elif blocking_scenario in [
            "Timeout exceeds (TE)",
            "Agrees equal disagrees (AED)",
            "Insufficient Agree Votes (IA)",
            "Excessive Disagree Votes (ED)",
        ]:
            return self.initiate_appeal()
        else:
            self.transaction_path.append(
                "Unknown blocking scenario. Transaction failed."
            )
            return False

    def process_leader_failure(self, scenario):
        """Handles scenarios where the leader fails (idle or timeout)."""
        if scenario == "Leader IDLE (LI)":
            penalty = self.fee_structure.get("leader_idle_penalty", 10)
            self.transaction_path.append("Leader is IDLE. Applying penalty.")
        else:
            penalty = self.fee_structure.get("leader_timeout_penalty", 0)
            self.transaction_path.append("Leader has timed out. Applying penalty.")

        self.leader.penalties += penalty
        self.transaction_path.append(f"Leader {self.leader.id} penalized {penalty}.")

        # Rotate leader
        self.rotate_leader()
        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            self.transaction_path.append(
                "Maximum leader rotations reached. Transaction failed."
            )
            return False
        else:
            return True  # Continue simulation

    def rotate_leader(self):
        """Rotates the leader to the next validator."""
        self.leader_index = (self.leader_index + 1) % len(self.validators_list)
        self.transaction_path.append(
            f"Leader rotated to Validator {self.validators_list[self.leader_index].id}."
        )

    def initiate_appeal(self):
        """Initiates an appeal by doubling the validator set."""
        if not self.appeal:
            self.transaction_path.append("No appeal initiated. Transaction failed.")
            return False

        current_validator_count = len(self.validators_list)
        if current_validator_count >= self.total_validators_available:
            self.transaction_path.append(
                "All validators have been included. Cannot appeal further."
            )
            self.transaction_path.append("Transaction failed.")
            return False
        else:
            self.double_validator_set()
            return True  # Continue simulation

    def double_validator_set(self):
        """Doubles the validator set during an appeal."""
        current_validator_count = len(self.validators_list)
        new_validator_count = min(
            current_validator_count * 2, self.total_validators_available
        )
        num_additional = new_validator_count - current_validator_count
        additional_validators = self.select_additional_validators(num_additional)
        self.validators_list.extend(additional_validators)
        self.N_r = len(self.validators_list)
        self.update_majority_threshold()
        self.max_retries = min(len(self.validators_list), 10)
        self.transaction_path.append(
            f"Validators doubled to {self.N_r}. New τr: {self.tau_r}."
        )

    def select_additional_validators(self, num_additional):
        """Selects additional validators without duplication."""
        existing_validator_ids = {validator.id for validator in self.validators_list}
        remaining_validators = [
            val for val in self.all_validators if val[0] not in existing_validator_ids
        ]
        if len(remaining_validators) == 0:
            return []  # No more validators to add
        num_additional = min(num_additional, len(remaining_validators))
        additional_validators = select_validators(num_additional, remaining_validators)
        return [Validator(id=val[0], stake=val[1]) for val in additional_validators]

    def penalize_violating_validators(self, violation_type):
        """Penalizes validators based on the violation type."""
        penalty_mapping = {
            VOTE_VIOLATION: self.fee_structure.get("validator_violation_penalty", 10),
            VOTE_IDLE: self.fee_structure.get("validator_idle_penalty", 5),
        }
        penalty = penalty_mapping.get(violation_type, 0)
        for validator in self.validators:
            if validator.last_vote == violation_type:
                validator.penalties += penalty
                self.transaction_path.append(
                    f"Validator {validator.id} penalized {penalty} for vote '{violation_type}'."
                )

    def distribute_rewards_and_penalties(self):
        """Distributes fees to leader and validators."""
        fees_info = distribute_fees(self.leader, self.validators, self.fee_structure)
        self.transaction_path.extend(fees_info)

    def output_results(self):
        """Outputs the transaction path and final fee distribution."""
        print("\nTransaction Path:")
        for step in self.transaction_path:
            print(step)

        print("\nFinal Fee Distribution:")
        total_fees = []
        leader_total = self.leader.rewards - self.leader.penalties
        total_fees.append(
            f"Leader (Validator {self.leader.id}) net fee: {leader_total} "
            f"(Rewards: {self.leader.rewards}, Penalties: {self.leader.penalties})"
        )
        for validator in self.validators:
            validator_total = validator.rewards - validator.penalties
            total_fees.append(
                f"Validator {validator.id} net fee: {validator_total} "
                f"(Rewards: {validator.rewards}, Penalties: {validator.penalties})"
            )
        for fee in total_fees:
            print(fee)

    def generate_mermaid_code(self):
        """Returns the generated Mermaid code."""
        mermaid_code = generate_mermaid_flowchart(self.transaction_path)
        return mermaid_code
