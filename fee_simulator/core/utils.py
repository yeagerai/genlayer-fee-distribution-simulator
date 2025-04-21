from functools import partial
from math import ceil
from typing import Dict, List

from fee_simulator.models.custom_types import (
    TransactionRoundResults,
    FeeDistribution,
    FeeEntry,
)
from fee_simulator.models.constants import (
    round_sizes,
    penalty_reward_coefficient,
    DEFAULT_STAKE,
    addresses_pool,
)


def initialize_fee_distribution() -> FeeDistribution:
    """Initialize a new fee distribution object."""
    fee_entries = {addr: FeeEntry() for addr in addresses_pool}
    return FeeDistribution(fees=fee_entries)


def compute_total_fees(fee_entry: FeeEntry) -> int:
    """Compute total fees for a FeeEntry, excluding stake."""
    return (
        fee_entry.leader_node
        + fee_entry.validator_node
        + fee_entry.sender_node
        + fee_entry.appealant_node
    )


def compute_appeal_bond(
    normal_round_index: int,
    round_sizes: list[int],
    penalty_reward_coefficient: int,
    leader_timeout: int,
    validators_timeout: int,
) -> int:
    """
    Compute appeal bond for a specific normal round's appeal.
    """
    safety_coefficient = 1.2

    if (
        normal_round_index % 2 != 0
        or normal_round_index < 0
        or normal_round_index >= len(round_sizes)
    ):
        raise ValueError(f"Invalid normal round index: {normal_round_index}")

    normal_size = round_sizes[normal_round_index]
    appeal_size = (
        round_sizes[normal_round_index + 1]
        if normal_round_index + 1 < len(round_sizes)
        else 0
    )
    next_normal_size = (
        round_sizes[normal_round_index + 2]
        if normal_round_index + 2 < len(round_sizes)
        else 0
    )

    base_penalty = penalty_reward_coefficient * validators_timeout
    appeal_cost = appeal_size * validators_timeout
    next_cost = next_normal_size * validators_timeout

    total_cost = appeal_cost + next_cost + leader_timeout

    minority_size = normal_size // 2
    penalty_offset = minority_size * base_penalty

    appeal_bond = ceil((total_cost - penalty_offset) * safety_coefficient)
    return max(appeal_bond, 0)


# Partial function with fixed round_sizes and penalty_reward_coefficient
compute_appeal_bond_partial = partial(
    compute_appeal_bond,
    round_sizes=round_sizes,
    penalty_reward_coefficient=penalty_reward_coefficient,
)


# Terminal colors
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        if color:
            return f"{color}{text}{cls.ENDC}"
        else:
            return text


def pretty_print_fee_distribution(fee_distribution: FeeDistribution) -> None:
    """
    Pretty prints the fee distribution for addresses that have non-zero fees
    or modified stakes.

    Args:
        fee_distribution: FeeDistribution object containing fees as FeeEntry objects
    """
    print(
        f"\n{Colors.BOLD}{Colors.HEADER}=== FEE DISTRIBUTION SUMMARY ==={Colors.ENDC}\n"
    )

    # Find the base stake value (usually the initial stake before any slashing)
    base_stake = DEFAULT_STAKE
    if any(
        fee_entry.stake != DEFAULT_STAKE for fee_entry in fee_distribution.fees.values()
    ):
        stake_values = [fee_entry.stake for fee_entry in fee_distribution.fees.values()]
        if stake_values:
            base_stake = max(stake_values)

    # Filter for addresses with non-zero fees or modified stakes
    active_addresses = []
    for addr, fee_entry in fee_distribution.fees.items():
        # Check if address has any non-zero fees
        has_non_zero_fees = any(
            fee != 0
            for fee in [
                fee_entry.leader_node,
                fee_entry.validator_node,
                fee_entry.sender_node,
                fee_entry.appealant_node,
            ]
        )

        # Check if stake has been modified (slashed)
        stake_modified = fee_entry.stake < (base_stake * 0.99)

        # Include address if it has fees or modified stake
        if has_non_zero_fees or stake_modified:
            active_addresses.append(addr)

    if not active_addresses:
        print(Colors.YELLOW + "No fees were distributed to any address." + Colors.ENDC)
        return

    # Display count of addresses with fees
    print(
        f"{Colors.CYAN}Active addresses: {len(active_addresses)} out of {len(fee_distribution.fees)}{Colors.ENDC}\n"
    )

    # Define role types
    roles = ["leader_node", "validator_node", "sender_node", "appealant_node", "stake"]

    # Calculate column width for consistent alignment
    column_width = 12

    # Create a line separator of appropriate length
    separator_length = 45 + 3 + (column_width + 3) * len(roles) + 3
    separator = "-" * separator_length

    # Print header
    header = (
        f"{Colors.BOLD}{'ADDRESS':<45} | "
        + " | ".join(f"{role.upper():<{column_width}}" for role in roles)
        + f" | TOTAL{Colors.ENDC}"
    )
    print(header)
    print(separator)

    # Print each active address
    for addr in active_addresses:
        fee_entry = fee_distribution.fees[addr]
        total_fees = (
            fee_entry.leader_node
            + fee_entry.validator_node
            + fee_entry.sender_node
            + fee_entry.appealant_node
        )  # Exclude stake from total

        # Format the address to show only first 10 and last 8 characters if too long
        if len(addr) > 30:
            formatted_addr = f"{addr[:10]}...{addr[-8:]}"
        else:
            formatted_addr = addr

        # Add slashing indicator if stake is lower than expected
        if fee_entry.stake < (base_stake * 0.99):
            formatted_addr += " " + Colors.RED + "[SLASHED]" + Colors.ENDC

        # Print the row with fees for each role, color-coded by value
        row_parts = []
        for role in roles:
            fee = getattr(fee_entry, role)
            if role == "stake":
                color = Colors.BLUE  # Stake in blue
            elif fee > 0:
                color = Colors.GREEN
            elif fee == 0:
                color = ""
            else:
                color = Colors.RED
            # Ensure consistent spacing with column_width
            row_parts.append(f"{Colors.colorize(str(fee), color):<{column_width}}")

        # Total is in bold green if positive
        total_color = ""
        if total_fees > 0:
            total_color = Colors.GREEN + Colors.BOLD
        elif total_fees < 0:
            total_color = Colors.RED + Colors.BOLD

        total_str = f"{Colors.colorize(str(total_fees), total_color)}"

        row = f"{formatted_addr:<45} | " + " | ".join(row_parts) + f" | {total_str}"
        print(row)

    # Print separator before totals
    print(separator)

    # Calculate and print totals
    total_by_role = {
        "leader_node": 0,
        "validator_node": 0,
        "sender_node": 0,
        "appealant_node": 0,
    }
    for addr in active_addresses:
        fee_entry = fee_distribution.fees[addr]
        for role in total_by_role:
            total_by_role[role] += getattr(fee_entry, role)

    grand_total = sum(total_by_role.values())

    total_row_parts = []
    for role in roles:
        if role != "stake":
            total = total_by_role[role]
            color = ""
            if total > 0:
                color = Colors.GREEN + Colors.BOLD
            elif total < 0:
                color = Colors.RED + Colors.BOLD
            total_row_parts.append(
                f"{Colors.colorize(str(total), color):<{column_width}}"
            )
        else:
            # Just show a dash for stake total
            total_row_parts.append(f"{'-':<{column_width}}")

    totals_row = (
        f"{Colors.BOLD}{'TOTAL':<45} | "
        + " | ".join(total_row_parts)
        + f" | {Colors.colorize(str(grand_total), Colors.GREEN + Colors.BOLD if grand_total >= 0 else Colors.RED + Colors.BOLD)}{Colors.ENDC}"
    )
    print(totals_row)


def pretty_print_transaction_results(
    transaction_results: TransactionRoundResults, round_labels: List[str] = None
) -> None:
    """
    Pretty prints the transaction results showing rounds, rotations and votes.

    Args:
        transaction_results: Transaction round results to display
        round_labels: Optional list of round labels corresponding to each round
    """
    print(f"\n{Colors.BOLD}{Colors.HEADER}=== TRANSACTION STRUCTURE ==={Colors.ENDC}\n")

    # Map round labels to colors for distinctive display
    label_colors = {
        "normal_round": Colors.GREEN,
        "empty_round": Colors.YELLOW,
        "appeal_leader_timeout_unsuccessful": Colors.RED,
        "appeal_leader_timeout_successful": Colors.CYAN,
        "appeal_leader_successful": Colors.BLUE,
        "appeal_leader_unsuccessful": Colors.RED,
        "appeal_validator_successful": Colors.BLUE,
        "appeal_validator_unsuccessful": Colors.RED,
        "leader_timeout": Colors.YELLOW,
        "skip_round": Colors.YELLOW,
        "leader_timeout_50_percent": Colors.CYAN,
        "split_previous_appeal_bond": Colors.CYAN,
        "leader_timeout_50_previous_appeal_bond": Colors.BLUE,
        "leader_timeout_150_previous_normal_round": Colors.GREEN,
    }

    for i, round_obj in enumerate(transaction_results.rounds):
        # Get label if available
        label = round_labels[i] if round_labels and i < len(round_labels) else None
        label_color = label_colors.get(label, Colors.ENDC) if label else Colors.ENDC

        # Display round number and label
        if label:
            print(
                f"{Colors.BOLD}{Colors.CYAN}Round {i}{Colors.ENDC} -- {label_color}{label}{Colors.ENDC}:"
            )
        else:
            print(f"{Colors.BOLD}{Colors.CYAN}Round {i}:{Colors.ENDC}")

        if not round_obj.rotations:
            print(f"  {Colors.YELLOW}Empty round - no rotations{Colors.ENDC}")
            continue

        for j, rotation in enumerate(round_obj.rotations):
            print(f"  {Colors.BOLD}Rotation {j}:{Colors.ENDC}")

            if not rotation.votes:
                print(f"    {Colors.YELLOW}No votes in this rotation{Colors.ENDC}")
                continue

            # Count vote types
            vote_counts = {
                "Agree": 0,
                "Disagree": 0,
                "Timeout": 0,
                "Idle": 0,
                "Leader": 0,
            }

            for addr, vote in rotation.votes.items():
                # Determine vote type and color
                if isinstance(vote, list):
                    if len(vote) == 3:
                        vote_display = f"{vote[0]}, {vote[1]}, {vote[2]}"
                    elif len(vote) == 2 and vote[0] not in [
                        "LeaderReceipt",
                        "LeaderTimeout",
                    ]:
                        vote_display = f"{vote[0]}, {vote[1]}"
                    else:
                        vote_display = f"{vote[0]}, {vote[1]}"
                    vote_type = (
                        vote[1]
                        if vote[0] in ["LeaderReceipt", "LeaderTimeout"]
                        else vote[0]
                    )
                    color = (
                        Colors.CYAN
                        if vote[0] in ["LeaderReceipt", "LeaderTimeout"]
                        else Colors.ENDC
                    )
                    vote_counts["Leader"] += 1
                else:
                    vote_display = vote
                    vote_type = vote
                    color = Colors.ENDC

                # Count normal votes
                if vote_type == "Agree":
                    color = Colors.GREEN
                    vote_counts["Agree"] += 1
                elif vote_type == "Disagree":
                    color = Colors.RED
                    vote_counts["Disagree"] += 1
                elif vote_type == "Timeout":
                    color = Colors.YELLOW
                    vote_counts["Timeout"] += 1
                elif vote_type == "Idle":
                    color = Colors.BLUE
                    vote_counts["Idle"] += 1

                # Format the address
                if len(addr) > 20:
                    formatted_addr = f"{addr[:8]}...{addr[-6:]}"
                else:
                    formatted_addr = addr

                print(f"    {formatted_addr}: {Colors.colorize(vote_display, color)}")

            # Display reserve votes if any
            if rotation.reserve_votes:
                print(f"    {Colors.BOLD}Reserve Votes:{Colors.ENDC}")
                for addr, vote in rotation.reserve_votes.items():
                    # Determine vote type and display for reserves
                    if isinstance(vote, list):
                        if len(vote) == 3:
                            vote_display = f"{vote[0]}, {vote[1]}, {vote[2]}"
                        elif len(vote) == 2 and vote[0] not in [
                            "LeaderReceipt",
                            "LeaderTimeout",
                        ]:
                            vote_display = f"{vote[0]}, {vote[1]}"
                        else:
                            vote_display = f"{vote[0]}, {vote[1]}"
                        vote_type = (
                            vote[1]
                            if vote[0] in ["LeaderReceipt", "LeaderTimeout"]
                            else vote[0]
                        )
                    else:
                        vote_display = vote
                        vote_type = vote

                    formatted_addr = (
                        f"{addr[:8]}...{addr[-6:]}" if len(addr) > 20 else addr
                    )
                    print(
                        f"      {formatted_addr}: {Colors.colorize(vote_display, Colors.BLUE)}"
                    )

            # Print vote summary
            print(f"\n    {Colors.BOLD}Vote Summary:{Colors.ENDC}")
            for vote_type, count in vote_counts.items():
                if count > 0:
                    if vote_type == "Agree":
                        color = Colors.GREEN
                    elif vote_type == "Disagree":
                        color = Colors.RED
                    elif vote_type == "Timeout":
                        color = Colors.YELLOW
                    elif vote_type == "Idle":
                        color = Colors.BLUE
                    elif vote_type == "Leader":
                        color = Colors.CYAN
                    print(f"      {vote_type}: {Colors.colorize(str(count), color)}")
            print("")  # Extra line for readability
