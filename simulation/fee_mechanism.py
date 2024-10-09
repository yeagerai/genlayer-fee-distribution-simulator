# simulator/fee_mechanism.py
from simulation.constants import UNIT_COST

fee_structure = {
    "LU": 1.0,  # Leader Units
    "VU": 1.0,  # Validator Units
    "leader_idle_penalty": 10.0,
    "leader_timeout_penalty": 0.0,
    "validator_violation_penalty": 10.0,
    "validator_idle_penalty": 5.0,
}


def distribute_fees(leader, validators, fee_structure):
    """Distributes fees to the leader and validators based on the fee structure."""
    fees_info = []
    LU = fee_structure.get("LU", 1)  # Leader Units
    VU = fee_structure.get("VU", 1)  # Validator Units
    leader_fee = LU * UNIT_COST
    validator_fee = VU * UNIT_COST

    # Leader gets leader fee
    leader.rewards += leader_fee
    fees_info.append(f"Leader {leader.id} assigned reward {leader_fee}")

    # Validators get validator fee
    for validator in validators:
        validator.rewards += validator_fee
    fees_info.append(f"Validators assigned reward {validator_fee} each")

    return fees_info
