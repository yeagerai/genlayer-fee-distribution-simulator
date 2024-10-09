# simulation/simulation.py

from simulation.constants import VOTE_AGREE, VOTE_IDLE, VOTE_TIMEOUT
from simulation.validator_selection import generate_validators_pool
from simulation.optimistic_democracy import TransactionSimulator
from simulation.fee_mechanism import fee_structure
from simulation.utils import set_random_seed

if __name__ == "__main__":
    # set_random_seed(42) # for reproducibility
    all_validators = generate_validators_pool()
    simulator = TransactionSimulator(
        all_validators=all_validators,
        r=0,
        leader_decision=VOTE_AGREE,
        appeal=True,
        fee_structure=fee_structure,
    )
    simulator.run_simulation()
