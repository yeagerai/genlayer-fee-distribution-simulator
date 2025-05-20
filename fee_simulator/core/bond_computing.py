from fee_simulator.constants import ROUND_SIZES


def compute_appeal_bond(
    normal_round_index: int,
    leader_timeout: int,
    validators_timeout: int,
) -> int:
    if (
        normal_round_index % 2 != 0
        or normal_round_index < 0
        or normal_round_index >= len(ROUND_SIZES)
    ):
        raise ValueError(f"Invalid normal round index: {normal_round_index}")

    next_normal_size = (
        ROUND_SIZES[normal_round_index + 2]
        if normal_round_index + 2 < len(ROUND_SIZES)
        else 0
    )

    next_cost = next_normal_size * validators_timeout

    total_cost = next_cost + leader_timeout

    return max(total_cost, 0)
