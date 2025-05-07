from typing import List
from fee_simulator.models import TransactionRoundResults, FeeEvent, TransactionBudget, RoundLabel
from fee_simulator.display.utils import (
    Colors,
    ROUND_LABEL_COLORS,
    ROLE_COLORS,
    format_address,
    create_table,
    colorize_financial,
)
from fee_simulator.fee_aggregators.address_metrics import (
    compute_total_costs,
    compute_total_earnings,
    compute_total_burnt,
    compute_total_slashed,
    compute_current_stake,
    compute_all_zeros,
)
from fee_simulator.constants import DEFAULT_STAKE

def display_summary_table(
    fee_events: List[FeeEvent],
    transaction_results: TransactionRoundResults,
    transaction_budget: TransactionBudget,
    round_labels: List[RoundLabel],
    verbose: bool = False,
) -> None:
    """
    Display a summary table of fee events, transaction budget, and round labels.

    Args:
        fee_events: List of FeeEvent objects.
        transaction_results: Transaction round results (unused but kept for interface).
        transaction_budget: Transaction budget parameters.
        round_labels: List of round labels.
        verbose: Enable detailed logging if True (currently unused).
    """
    print(f"\n{Colors.BOLD}{Colors.HEADER}=== SUMMARY TABLE ==={Colors.ENDC}\n")

    # Collect active addresses
    active_addresses = {
        event.address for event in fee_events
        if not compute_all_zeros(fee_events, event.address)
    }

    # Main summary table
    headers = [
        "ADDRESS",
        "ROLE",
        "COST",
        "EARNED",
        "SLASHED",
        "BURNED",
        "STAKED",
        "NET",
        "ROUNDS",
    ]
    table_data = []
    totals = {
        "cost": 0,
        "earned": 0,
        "slashed": 0,
        "burned": 0,
        "staked": 0,
        "net": 0,
    }

    for addr in sorted(active_addresses):
        addr_short = format_address(addr)
        roles = {event.role for event in fee_events if event.address == addr and event.role is not None}
        role_display = ", ".join(Colors.colorize(role, ROLE_COLORS.get(role, Colors.ENDC)) for role in sorted(roles)) if roles else "NONE"
        cost = compute_total_costs(fee_events, addr)
        earned = compute_total_earnings(fee_events, addr)
        slashed = compute_total_slashed(fee_events, addr)
        burned = compute_total_burnt(fee_events, addr)
        staked = compute_current_stake(addr, fee_events)
        net = earned - cost - slashed - burned
        rounds = sorted({event.round_index for event in fee_events if event.address == addr and event.round_index is not None})

        if staked < (DEFAULT_STAKE * 0.99):
            addr_short += Colors.colorize(" [SLASHED]", Colors.RED)

        table_data.append([
            addr_short,
            role_display,
            colorize_financial(cost, negative_color=Colors.RED),
            colorize_financial(earned, positive_color=Colors.GREEN),
            colorize_financial(slashed, negative_color=Colors.RED),
            colorize_financial(burned, negative_color=Colors.RED),
            colorize_financial(staked, positive_color=Colors.BLUE),
            colorize_financial(net),
            ", ".join(str(r) for r in rounds) if rounds else "-",
        ])

        totals["cost"] += cost
        totals["earned"] += earned
        totals["slashed"] += slashed
        totals["burned"] += burned
        totals["staked"] += staked
        totals["net"] += net

    # Add totals row
    table_data.append([
        Colors.BOLD + "TOTAL" + Colors.ENDC,
        "-",
        colorize_financial(totals["cost"], negative_color=Colors.RED),
        colorize_financial(totals["earned"], positive_color=Colors.GREEN),
        colorize_financial(totals["slashed"], negative_color=Colors.RED),
        colorize_financial(totals["burned"], negative_color=Colors.RED),
        colorize_financial(totals["staked"], positive_color=Colors.BLUE),
        colorize_financial(totals["net"]),
        "-",
    ])

    create_table(headers=headers, data=table_data)

    # Budget summary table
    budget_data = [
        ["Leader Timeout", Colors.colorize(str(transaction_budget.leaderTimeout), Colors.CYAN)],
        ["Validators Timeout", Colors.colorize(str(transaction_budget.validatorsTimeout), Colors.CYAN)],
        ["Appeal Rounds", Colors.colorize(str(transaction_budget.appealRounds), Colors.CYAN)],
        ["Sender Address", format_address(transaction_budget.senderAddress)],
    ]
    if transaction_budget.appeals:
        budget_data.append(["Appeals", ", ".join(format_address(a.appealantAddress) for a in transaction_budget.appeals)])
    create_table(headers=["PARAMETER", "VALUE"], data=budget_data, title="Transaction Budget Summary")

    # Round labels table
    round_data = [
        [i, Colors.colorize(label, ROUND_LABEL_COLORS.get(label, Colors.YELLOW))]
        for i, label in enumerate(round_labels)
    ]
    create_table(headers=["ROUND", "LABEL"], data=round_data, title="Round Labels")