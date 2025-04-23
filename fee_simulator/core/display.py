import logging
from typing import List, Optional
from tabulate import tabulate
from fee_simulator.models.custom_types import TransactionRoundResults, FeeDistribution
from fee_simulator.models.constants import DEFAULT_STAKE


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
        return f"{color}{text}{cls.ENDC}" if color else text


# Configure logging
def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def _format_address(addr: str, max_len: int = 20) -> str:
    """Format address to show first 8 and last 6 characters if too long."""
    return f"{addr[:8]}...{addr[-6:]}" if len(addr) > max_len else addr


def _get_vote_display_and_type(vote, is_leader: bool = False) -> tuple[str, str, str]:
    """Extract vote display string, type, and color."""
    if isinstance(vote, list):
        vote_display = ", ".join(str(v) for v in vote)
        vote_type = vote[1] if is_leader else vote[0]
        color = Colors.CYAN if is_leader else Colors.ENDC
    else:
        vote_display = vote
        vote_type = vote
        color = Colors.ENDC

    if vote_type == "Agree":
        color = Colors.GREEN
    elif vote_type == "Disagree":
        color = Colors.RED
    elif vote_type == "Timeout":
        color = Colors.YELLOW
    elif vote_type == "Idle":
        color = Colors.BLUE
    return vote_display, vote_type, color


def _build_vote_table(votes: dict, is_reserve: bool = False) -> list:
    """Build table data for votes or reserve votes."""
    table_data = []
    for addr, vote in votes.items():
        is_leader = (
            vote[0] in ["LeaderReceipt", "LeaderTimeout"]
            if isinstance(vote, list)
            else False
        )
        vote_display, _, color = _get_vote_display_and_type(vote, is_leader)
        addr_short = _format_address(addr)
        table_data.append(
            [
                addr_short,
                Colors.colorize(vote_display, Colors.BLUE if is_reserve else color),
            ]
        )
    return table_data


def _build_vote_summary(votes: dict) -> tuple[list, dict]:
    """Build vote summary table and counts."""
    vote_counts = {
        "Agree": 0,
        "Disagree": 0,
        "Timeout": 0,
        "Idle": 0,
        "Leader": 0,
        "NA": 0,
    }
    for vote in votes.values():
        is_leader = isinstance(vote, list) and vote[0] in [
            "LeaderReceipt",
            "LeaderTimeout",
        ]
        _, vote_type, _ = _get_vote_display_and_type(vote, is_leader)
        vote_counts[vote_type] += 1
        if is_leader:
            vote_counts["Leader"] += 1

    summary_data = [
        [
            k,
            Colors.colorize(
                str(v),
                (
                    Colors.GREEN
                    if k == "Agree"
                    else (
                        Colors.RED
                        if k == "Disagree"
                        else (
                            Colors.YELLOW
                            if k == "Timeout"
                            else Colors.BLUE if k == "Idle" else Colors.CYAN
                        )
                    )
                ),
            ),
        ]
        for k, v in vote_counts.items()
        if v > 0
    ]
    return summary_data, vote_counts


def pretty_print_transaction_results(
    transaction_results: TransactionRoundResults,
    round_labels: Optional[List[str]] = None,
    verbose: bool = False,
) -> None:
    """
    Pretty print transaction results with formatted tables.

    Args:
        transaction_results: Transaction round results to display.
        round_labels: Optional list of round labels.
        verbose: Enable detailed logging if True.
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    logger.info("Printing transaction results")

    print(f"\n{Colors.BOLD}{Colors.HEADER}=== TRANSACTION STRUCTURE ==={Colors.ENDC}\n")

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
        label = (
            round_labels[i] if round_labels and i < len(round_labels) else f"Round {i}"
        )
        label_color = (
            label_colors.get(label, Colors.ENDC)
            if label != f"Round {i}"
            else Colors.CYAN
        )
        print(
            f"{Colors.BOLD}{Colors.CYAN}Round {i}{Colors.ENDC} -- {label_color}{label}{Colors.ENDC}:"
        )

        if not round_obj.rotations:
            print(f"  {Colors.YELLOW}Empty round - no rotations{Colors.ENDC}")
            continue

        for j, rotation in enumerate(round_obj.rotations):
            logger.debug(f"Processing rotation {j} in round {i}")
            print(f"  {Colors.BOLD}Rotation {j}:{Colors.ENDC}")

            if not rotation.votes:
                print(f"    {Colors.YELLOW}No votes in this rotation{Colors.ENDC}")
                continue

            # Votes table
            table_data = _build_vote_table(rotation.votes)
            print(
                tabulate(table_data, headers=["Address", "Vote"], tablefmt="fancy_grid")
            )

            # Reserve votes
            if rotation.reserve_votes:
                print(f"\n  {Colors.BOLD}Reserve Votes:{Colors.ENDC}")
                reserve_table = _build_vote_table(
                    rotation.reserve_votes, is_reserve=True
                )
                print(
                    tabulate(
                        reserve_table,
                        headers=["Address", "Vote"],
                        tablefmt="fancy_grid",
                    )
                )

            # Vote summary
            summary_data, _ = _build_vote_summary(rotation.votes)
            print(f"\n  {Colors.BOLD}Vote Summary:{Colors.ENDC}")
            print(
                tabulate(
                    summary_data, headers=["Vote Type", "Count"], tablefmt="fancy_grid"
                )
            )
            print("")


def pretty_print_fee_distribution(
    fee_distribution: FeeDistribution, verbose: bool = False
) -> None:
    """
    Pretty print fee distribution with a formatted table.

    Args:
        fee_distribution: FeeDistribution object containing fees.
        verbose: Enable detailed logging if True.
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    logger.info("Printing fee distribution")

    print(
        f"\n{Colors.BOLD}{Colors.HEADER}=== FEE DISTRIBUTION SUMMARY ==={Colors.ENDC}\n"
    )

    # Find base stake
    base_stake = max(
        (fee_entry.stake for fee_entry in fee_distribution.fees.values()),
        default=DEFAULT_STAKE,
    )

    # Filter active addresses
    active_addresses = [
        addr
        for addr, fee_entry in fee_distribution.fees.items()
        if any(
            fee != 0
            for fee in [
                fee_entry.leader_node,
                fee_entry.validator_node,
                fee_entry.sender_node,
                fee_entry.appealant_node,
            ]
        )
        or fee_entry.stake < (base_stake * 0.99)
    ]

    if not active_addresses:
        print(Colors.YELLOW + "No fees were distributed to any address." + Colors.ENDC)
        return

    print(
        f"{Colors.CYAN}Active addresses: {len(active_addresses)} out of {len(fee_distribution.fees)}{Colors.ENDC}\n"
    )

    # Prepare table
    headers = [
        "ADDRESS",
        "LEADER_NODE",
        "VALIDATOR_NODE",
        "SENDER_NODE",
        "APPEALANT_NODE",
        "STAKE",
        "TOTAL",
    ]
    table_data = []
    totals = {
        "leader_node": 0,
        "validator_node": 0,
        "sender_node": 0,
        "appealant_node": 0,
        "total": 0,
    }

    for addr in active_addresses:
        fee_entry = fee_distribution.fees[addr]
        total_fees = (
            fee_entry.leader_node
            + fee_entry.validator_node
            + fee_entry.sender_node
            + fee_entry.appealant_node
        )
        addr_short = _format_address(addr, max_len=30)
        if fee_entry.stake < (base_stake * 0.99):
            addr_short += Colors.colorize(" [SLASHED]", Colors.RED)

        row = [
            addr_short,
            Colors.colorize(
                str(fee_entry.leader_node),
                (
                    Colors.GREEN
                    if fee_entry.leader_node > 0
                    else Colors.RED if fee_entry.leader_node < 0 else ""
                ),
            ),
            Colors.colorize(
                str(fee_entry.validator_node),
                (
                    Colors.GREEN
                    if fee_entry.validator_node > 0
                    else Colors.RED if fee_entry.validator_node < 0 else ""
                ),
            ),
            Colors.colorize(
                str(fee_entry.sender_node),
                (
                    Colors.GREEN
                    if fee_entry.sender_node > 0
                    else Colors.RED if fee_entry.sender_node < 0 else ""
                ),
            ),
            Colors.colorize(
                str(fee_entry.appealant_node),
                (
                    Colors.GREEN
                    if fee_entry.appealant_node > 0
                    else Colors.RED if fee_entry.appealant_node < 0 else ""
                ),
            ),
            Colors.colorize(str(fee_entry.stake), Colors.BLUE),
            Colors.colorize(
                str(total_fees),
                (
                    Colors.GREEN + Colors.BOLD
                    if total_fees > 0
                    else Colors.RED + Colors.BOLD if total_fees < 0 else Colors.BOLD
                ),
            ),
        ]
        table_data.append(row)

        # Update totals
        for role in totals:
            if role != "total":
                totals[role] += getattr(fee_entry, role)
        totals["total"] += total_fees

    # Totals row
    table_data.append(
        [
            Colors.BOLD + "TOTAL" + Colors.ENDC,
            Colors.colorize(
                str(totals["leader_node"]),
                (
                    Colors.GREEN + Colors.BOLD
                    if totals["leader_node"] > 0
                    else (
                        Colors.RED + Colors.BOLD
                        if totals["leader_node"] < 0
                        else Colors.BOLD
                    )
                ),
            ),
            Colors.colorize(
                str(totals["validator_node"]),
                (
                    Colors.GREEN + Colors.BOLD
                    if totals["validator_node"] > 0
                    else (
                        Colors.RED + Colors.BOLD
                        if totals["validator_node"] < 0
                        else Colors.BOLD
                    )
                ),
            ),
            Colors.colorize(
                str(totals["sender_node"]),
                (
                    Colors.GREEN + Colors.BOLD
                    if totals["sender_node"] > 0
                    else (
                        Colors.RED + Colors.BOLD
                        if totals["sender_node"] < 0
                        else Colors.BOLD
                    )
                ),
            ),
            Colors.colorize(
                str(totals["appealant_node"]),
                (
                    Colors.GREEN + Colors.BOLD
                    if totals["appealant_node"] > 0
                    else (
                        Colors.RED + Colors.BOLD
                        if totals["appealant_node"] < 0
                        else Colors.BOLD
                    )
                ),
            ),
            "-",
            Colors.colorize(
                str(totals["total"]),
                (
                    Colors.GREEN + Colors.BOLD
                    if totals["total"] >= 0
                    else Colors.RED + Colors.BOLD
                ),
            ),
        ]
    )

    print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
