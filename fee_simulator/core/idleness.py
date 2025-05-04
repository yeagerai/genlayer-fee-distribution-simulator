from typing import List
from fee_simulator.models import (
    TransactionRoundResults,
    FeeEvent,
    Round,
    Rotation
)

from fee_simulator.core.majority import (
    normalize_vote,
)

from fee_simulator.fee_aggregators.address_metrics import compute_current_stake

def replace_idle_participants(
    fee_events: List[FeeEvent],
    transaction_results: TransactionRoundResults,
) -> tuple[TransactionRoundResults, List[FeeEvent]]:
    new_fee_events = fee_events
    new_event_index = len(new_fee_events)

    for i, round_obj in enumerate(transaction_results.rounds):
        if round_obj.rotations:
            rotation = round_obj.rotations[-1]
            votes = rotation.votes

            # Find idle validators
            idle_addresses = [
                addr for addr, vote in votes.items() if normalize_vote(vote) == "Idle"
            ]

            # Slash idle validators
            for addr in idle_addresses:
                current_stake = compute_current_stake(addr, new_fee_events)
                new_fee_events.append(FeeEvent(
                    sequence_id=new_event_index,
                    address=addr,
                    slashed=current_stake * 0.01,
                ))
                new_event_index += 1

            # Replace idle validators with reserves
            if idle_addresses:
                new_votes = {
                    addr: vote
                    for addr, vote in votes.items()
                    if normalize_vote(vote) != "Idle"
                }
                reserve_count = len(idle_addresses)

                # Find available reserves
                available_reserves = [
                    addr
                    for addr, vote in rotation.reserve_votes.items()
                    if addr not in new_votes
                ]

                # Add reserves to replace idle validators
                for i in range(min(reserve_count, len(available_reserves))):
                    reserve_addr = available_reserves[i]
                    new_votes[reserve_addr] = rotation.reserve_votes[reserve_addr]

                   
                # Update votes in the rotation
                rotation.votes = new_votes

                new_round = Round(
                    rotations=[Rotation(
                        votes=new_votes,
                        reserve_votes=rotation.reserve_votes,
                    )],
                )
            new_transaction_results = TransactionRoundResults(
                rounds=[new_round],
            )

    return new_transaction_results, new_fee_events
