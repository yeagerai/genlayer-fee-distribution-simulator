from functools import partial
from math import ceil
import random
import string
import hashlib
from typing import Dict, List

from custom_types import TransactionRoundResults
from constants import round_sizes, penalty_reward_coefficient


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

    @staticmethod
    def colorize(text, color):
        return f"{color}{text}{Colors.ENDC}"


def generate_random_address() -> str:
    """
    Generate a random Ethereum-style address.

    Returns:
        A random Ethereum address string
    """
    # Create random string as seed
    seed = "".join(random.choices(string.ascii_letters + string.digits, k=32))
    # Hash it with SHA-256
    hashed = hashlib.sha256(seed.encode()).hexdigest()
    # Format as Ethereum address (0x + 40 hex chars)
    return "0x" + hashed[:40]


def pretty_print_fee_distribution(fee_distribution: Dict[str, Dict[str, int]]) -> None:
    """
    Pretty prints the fee distribution for addresses that have non-zero fees
    in at least one field.

    Args:
        fee_distribution: Dictionary mapping addresses to fee entries
    """
    print(
        f"\n{Colors.BOLD}{Colors.HEADER}=== FEE DISTRIBUTION SUMMARY ==={Colors.ENDC}\n"
    )

    # Find addresses with non-zero fees
    active_addresses = []
    for addr, roles in fee_distribution.items():
        has_fees = any(fee != 0 for fee in roles.values())
        if has_fees:
            active_addresses.append(addr)

    if not active_addresses:
        print(Colors.YELLOW + "No fees were distributed to any address." + Colors.ENDC)
        return

    # Display count of addresses with fees
    print(
        f"{Colors.CYAN}Total addresses with fees: {len(active_addresses)} out of {len(fee_distribution)}{Colors.ENDC}\n"
    )

    # Get all role types from the first address (assuming all addresses have the same roles)
    roles = list(fee_distribution[active_addresses[0]].keys())

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

    # Print each address with non-zero fees
    for addr in active_addresses:
        roles_fees = fee_distribution[addr]
        total_fees = sum(roles_fees.values())

        # Format the address to show only first 10 and last 8 characters if too long
        if len(addr) > 30:
            formatted_addr = f"{addr[:10]}...{addr[-8:]}"
        else:
            formatted_addr = addr

        # Print the row with fees for each role, color-coded by value
        row_parts = []
        for role in roles:
            fee = roles_fees[role]
            if fee > 0:
                color = Colors.GREEN
            elif fee == 0:
                color = ""
            else:
                color = Colors.RED
            # Ensure consistent spacing with column_width
            row_parts.append(f"{Colors.colorize(str(fee), color):<{column_width}}")

        # Total is in bold green if positive
        total_color = Colors.GREEN + Colors.BOLD if total_fees > 0 else ""
        total_str = f"{Colors.colorize(str(total_fees), total_color)}"

        row = f"{formatted_addr:<45} | " + " | ".join(row_parts) + f" | {total_str}"
        print(row)

    # Print separator before totals
    print(separator)

    # Calculate and print totals
    total_by_role = {
        role: sum(fee_distribution[addr][role] for addr in active_addresses)
        for role in roles
    }
    grand_total = sum(total_by_role.values())

    total_row_parts = []
    for role in roles:
        total = total_by_role[role]
        color = Colors.GREEN + Colors.BOLD if total > 0 else ""
        total_row_parts.append(f"{Colors.colorize(str(total), color):<{column_width}}")

    totals_row = (
        f"{Colors.BOLD}{'TOTAL':<45} | "
        + " | ".join(total_row_parts)
        + f" | {Colors.colorize(str(grand_total), Colors.GREEN + Colors.BOLD)}{Colors.ENDC}"
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
                    vote_display = f"{vote[0]}, {vote[1]}"
                    vote_type = vote[1]
                    color = Colors.CYAN  # Leader votes in cyan
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
