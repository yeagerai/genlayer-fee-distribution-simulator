from typing import List

from fee_simulator.models import (
    TransactionBudget,
    TransactionRoundResults,
    FeeEvent,
)

from fee_simulator.types import (
    RoundLabel,
)

from fee_simulator.utils import (
    compute_appeal_bond_partial,
    compute_total_cost,
    compute_total_fees,
    initialize_constant_stakes,
)

from fee_simulator.core.round_labeling import label_rounds
from fee_simulator.core.idleness import replace_idle_participants
from fee_simulator.core.deterministic_violation import handle_deterministic_violations
from fee_simulator.core.round_fee_distribution import distribute_round


def process_transaction(
    addresses: List[str],
    transaction_results: TransactionRoundResults,
    transaction_budget: TransactionBudget,
) -> tuple[List[FeeEvent], List[RoundLabel]]:

    fee_events = []
    last_event_index = 0

    # Subtract total cost from sender address
    sender_address = transaction_budget.senderAddress
    fee_events.append(FeeEvent(
        sequence_id=last_event_index,
        address=sender_address,
        cost=compute_total_cost(transaction_budget),
    ))
    last_event_index += 1
    # Initialize stakes
    fee_events.extend(initialize_constant_stakes(last_event_index, addresses))
    last_event_index = len(fee_events)

    # Replace idle validators and slash them
    replace_idle_transaction_results, replace_idle_fee_events = replace_idle_participants(
        fee_events=fee_events,
        transaction_results=transaction_results,
    )
    fee_events = replace_idle_fee_events
    last_event_index = len(fee_events)

    # Handle deterministic violations (hash mismatches)
    fee_events.extend(handle_deterministic_violations(
        replace_idle_transaction_results, last_event_index
    ))
    last_event_index = len(fee_events)

    # Get labels for all rounds
    labels = label_rounds(replace_idle_transaction_results)

    # Process each round with its label
    for i, round_obj in enumerate(replace_idle_transaction_results.rounds):
        if i < len(labels):

            # Subtract appeal bond from appealant address
            if i % 2 == 1:
                appealant_address = transaction_budget.appeals[i // 2].appealantAddress
                bond = compute_appeal_bond_partial(
                    normal_round_index=i - 1,
                    leader_timeout=transaction_budget.leaderTimeout,
                    validators_timeout=transaction_budget.validatorsTimeout,
                )
                fee_distribution.fees[appealant_address].appealant_node -= bond

            fee_distribution = distribute_round(
                round=round_obj,
                round_index=i,
                label=labels[i],
                transaction_budget=transaction_budget,
                fee_distribution=fee_distribution,
            )

    # Refund sender negative fees if necessary
    # TODO: toppers (users that top up the transaction) should be refunded proportionally to their spending
    print(fee_distribution.fees[sender_address].sender_node)
    positive_fees = {
        addr: compute_total_fees(fee)
        for addr, fee in fee_distribution.fees.items()
        if compute_total_fees(fee) > 0
    }
    appealant_addresses = [
        transaction_budget.appeals[i // 2].appealantAddress
        for i in range(len(transaction_budget.appeals) * 2)
    ]
    negative_fees_but_sender = {
        addr: compute_total_fees(fee)
        for addr, fee in fee_distribution.fees.items()
        if compute_total_fees(fee) < 0 and addr != transaction_budget.senderAddress and addr not in appealant_addresses
    }
    print(negative_fees_but_sender)
    have_to_pay = -1 * (
        sum(negative_fees_but_sender.values()) + sum(positive_fees.values())
    )
    print(sum(negative_fees_but_sender.values()), have_to_pay, sum(positive_fees.values()))
    refund = compute_total_cost(transaction_budget) + have_to_pay
    if refund > 0:
        fee_distribution.fees[transaction_budget.senderAddress].sender_node += refund

        if fee_distribution.fees[transaction_budget.senderAddress].sender_node > 0:
            tokens_to_burn = fee_distribution.fees[
                transaction_budget.senderAddress
            ].sender_node
            fee_distribution.fees[transaction_budget.senderAddress].sender_node = 0

    return fee_distribution, labels
