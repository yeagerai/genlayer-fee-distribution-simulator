from typing import List
from fee_simulator.models import TransactionRoundResults, RoundLabel
from fee_simulator.display.utils import Colors, ROUND_LABEL_COLORS, VOTE_TYPE_COLORS, format_address, format_vote, create_table, get_vote_summary

def display_transaction_results(
    transaction_results: TransactionRoundResults,
    round_labels: List[RoundLabel],
    verbose: bool = False,
) -> None:
    """
    Display transaction results with formatted tables for rounds, rotations, and votes.

    Args:
        transaction_results: Transaction round results to display.
        round_labels: List of round labels.
        verbose: Enable detailed logging if True (currently unused).
    """
    print(f"\n{Colors.BOLD}{Colors.HEADER}=== TRANSACTION RESULTS ==={Colors.ENDC}\n")

    for round_idx, round_obj in enumerate(transaction_results.rounds):
        # Display round header with label
        label = round_labels[round_idx] if round_idx < len(round_labels) else f"Round {round_idx}"
        label_color = ROUND_LABEL_COLORS.get(label, Colors.CYAN)
        print(f"{Colors.BOLD}{Colors.CYAN}Round {round_idx}{Colors.ENDC} -- {Colors.colorize(label, label_color)}:")

        if not round_obj.rotations:
            print(f"  {Colors.YELLOW}Empty round - no rotations{Colors.ENDC}")
            continue

        for rotation_idx, rotation in enumerate(round_obj.rotations):
            print(f"  {Colors.BOLD}Rotation {rotation_idx}:{Colors.ENDC}")

            if not rotation.votes:
                print(f"    {Colors.YELLOW}No votes in this rotation{Colors.ENDC}")
                continue

            # Votes table
            vote_data = []
            for addr, vote in rotation.votes.items():
                is_leader = isinstance(vote, list) and vote[0] in ["LEADER_RECEIPT", "LEADER_TIMEOUT"]
                vote_display, vote_type = format_vote(vote, is_leader)
                vote_color = VOTE_TYPE_COLORS.get(vote_type, Colors.ENDC)
                if is_leader:
                    vote_color = Colors.CYAN
                vote_data.append([
                    format_address(addr),
                    Colors.colorize(vote_display, vote_color),
                ])
            create_table(headers=["ADDRESS", "VOTE"], data=vote_data)

            # Reserve votes table
            if rotation.reserve_votes:
                reserve_data = []
                for addr, vote in rotation.reserve_votes.items():
                    vote_display, _ = format_vote(vote)
                    reserve_data.append([
                        format_address(addr),
                        Colors.colorize(vote_display, Colors.BLUE),
                    ])
                create_table(headers=["ADDRESS", "RESERVE VOTE"], data=reserve_data, title="Reserve Votes")

            # Vote summary table
            summary_data = get_vote_summary(rotation.votes)
            create_table(headers=["VOTE TYPE", "COUNT"], data=summary_data, title="Vote Summary")