from fee_simulator.models import (
    Round,
    TransactionBudget,
    FeeEvent,
)

from fee_simulator.types import (
    RoundLabel,
)

from fee_simulator.core.majority import (
    compute_majority,
    who_is_in_vote_majority,
)

from fee_simulator.utils import (
    compute_appeal_bond_partial,
)

def distribute_round(
    round: Round,
    round_index: int,
    label: RoundLabel,
    transaction_budget: TransactionBudget,
    fee_distribution: FeeDistribution,
) -> FeeDistribution:
    """
    Distribute fees for a single round based on its label.

    Args:
        round: Round data with rotations
        round_index: Index of the round
        label: Round label
        transaction_budget: Transaction budget parameters
        fee_distribution: Current fee distribution

    Returns:
        Updated fee distribution
    """
    # Skip processing for certain round types
    if label == "empty_round" or label == "skip_round":
        return fee_distribution

    # If round has no rotations, return unchanged
    if not round.rotations:
        return fee_distribution

    # Get the votes from the last rotation
    votes = round.rotations[-1].votes

    # Get appeal bond for this round if it's an appeal round
    appeal_bond = 0
    if (
        round_index % 2 == 1
        and transaction_budget.appeals
        and round_index // 2 < len(transaction_budget.appeals)
    ):
        normal_round_idx = round_index - 1  # Previous normal round
        appeal_bond = compute_appeal_bond_partial(
            normal_round_index=normal_round_idx,
            leader_timeout=transaction_budget.leaderTimeout,
            validators_timeout=transaction_budget.validatorsTimeout,
        )

    if label == "normal_round":
        majority = compute_majority(votes)
        if majority == "UNDETERMINED":  # equal split

            # TODO: Check Deterministic Violation Majority and slash leader if it is
            # Get first address as leader
            first_addr = next(iter(votes.keys()), None)
            if first_addr:
                if first_addr in fee_distribution.fees:
                    fee_distribution.fees[
                        first_addr
                    ].leader_node += transaction_budget.leaderTimeout

                # Distribute to all validators
                for addr in votes.keys():
                    if addr in fee_distribution.fees:
                        fee_distribution.fees[
                            addr
                        ].validator_node += transaction_budget.validatorsTimeout
        else:
            # Get addresses in majority
            majority_addresses, minority_addresses = who_is_in_vote_majority(
                votes, majority
            )
            # Distribute to majority validators
            for addr in majority_addresses:
                if addr in fee_distribution.fees:
                    fee_distribution.fees[
                        addr
                    ].validator_node += transaction_budget.validatorsTimeout

            # Distribute to minority validators
            for addr in minority_addresses:
                if addr in fee_distribution.fees:
                    fee_distribution.fees[addr].validator_node -= (
                        penalty_reward_coefficient
                        * transaction_budget.validatorsTimeout
                    )

            # Give leader fee to first address
            first_addr = next(iter(votes.keys()), None)
            if first_addr and first_addr in fee_distribution.fees:
                fee_distribution.fees[
                    first_addr
                ].leader_node += transaction_budget.leaderTimeout

    elif label == "validators_penalty_only_round":
        penalizable_votes = ["Disagree", "Timeout"]
        penalizable_addresses = [
            addr
            for addr in votes.keys()
            if normalize_vote(votes[addr]) in penalizable_votes
        ]

        for addr in penalizable_addresses:
            if addr in fee_distribution.fees:
                fee_distribution.fees[addr].validator_node -= (
                    penalty_reward_coefficient * transaction_budget.validatorsTimeout
                )

    elif label == "appeal_leader_timeout_unsuccessful":
        sender_address = transaction_budget.senderAddress

        # Ensure round_index is valid for appeals
        if transaction_budget.appeals and round_index <= len(
            transaction_budget.appeals
        ):
            appeal = transaction_budget.appeals[floor(round_index / 2)]
            appealant_address = appeal.appealantAddress

            # Update fees
            if sender_address in fee_distribution.fees:
                fee_distribution.fees[sender_address].sender_node += appeal_bond

            if appealant_address in fee_distribution.fees:
                fee_distribution.fees[appealant_address].appealant_node -= appeal_bond

    elif label == "appeal_leader_timeout_successful":
        # Ensure round_index is valid for appeals
        if transaction_budget.appeals and round_index <= len(
            transaction_budget.appeals
        ):
            appeal = transaction_budget.appeals[floor(round_index / 2)]
            appealant_address = appeal.appealantAddress

            if appealant_address in fee_distribution.fees:
                fee_distribution.fees[appealant_address].appealant_node += appeal_bond
                fee_distribution.fees[appealant_address].appealant_node += (
                    transaction_budget.leaderTimeout / 2
                )

    elif label == "appeal_leader_successful":
        # Ensure round_index is valid for appeals
        if transaction_budget.appeals and round_index <= len(
            transaction_budget.appeals
        ):
            appeal = transaction_budget.appeals[floor(round_index / 2)]
            appealant_address = appeal.appealantAddress

            if appealant_address in fee_distribution.fees:
                fee_distribution.fees[appealant_address].appealant_node += appeal_bond
                fee_distribution.fees[
                    appealant_address
                ].appealant_node += transaction_budget.leaderTimeout

    elif label == "appeal_leader_unsuccessful":
        """Appealant bond is subtracted at the beginning of the process, and sender
        gets refunded at the end of the process"""

    elif label == "appeal_validator_successful":
        # Ensure round_index is valid for appeals
        if transaction_budget.appeals and round_index <= len(
            transaction_budget.appeals
        ):
            appeal = transaction_budget.appeals[floor(round_index / 2)]
            appealant_address = appeal.appealantAddress

            if appealant_address in fee_distribution.fees:
                fee_distribution.fees[appealant_address].appealant_node += appeal_bond
                fee_distribution.fees[
                    appealant_address
                ].appealant_node += transaction_budget.leaderTimeout

            majority = compute_majority(votes)
            majority_addresses, minority_addresses = who_is_in_vote_majority(
                votes, majority
            )

            # Distribute to all validators
            for addr in majority_addresses:
                if addr in fee_distribution.fees:
                    fee_distribution.fees[
                        addr
                    ].validator_node += transaction_budget.validatorsTimeout

            # Add penalty for minority validators
            for addr in minority_addresses:
                if addr in fee_distribution.fees:
                    fee_distribution.fees[addr].validator_node -= (
                        penalty_reward_coefficient
                        * transaction_budget.validatorsTimeout
                    )

    elif label == "appeal_validator_unsuccessful":
        sender_address = transaction_budget.senderAddress

        # Ensure round_index is valid for appeals
        if transaction_budget.appeals and round_index <= len(
            transaction_budget.appeals
        ):
            appeal = transaction_budget.appeals[floor(round_index / 2)]
            appealant_address = appeal.appealantAddress

            majority = compute_majority(votes)
            majority_addresses, minority_addresses = who_is_in_vote_majority(
                votes, majority
            )

            # Distribute to all validators
            for addr in majority_addresses:
                if addr in fee_distribution.fees:
                    fee_distribution.fees[
                        addr
                    ].validator_node += transaction_budget.validatorsTimeout

            # Add penalty for minority validators
            for addr in minority_addresses:
                if addr in fee_distribution.fees:
                    fee_distribution.fees[addr].validator_node -= (
                        penalty_reward_coefficient
                        * transaction_budget.validatorsTimeout
                    )


    elif label == "leader_timeout_50_percent":
        first_addr = next(iter(votes.keys()), None)
        if first_addr and first_addr in fee_distribution.fees:
            fee_distribution.fees[first_addr].leader_node += (
                transaction_budget.leaderTimeout / 2
            )

    elif label == "split_previous_appeal_bond":
        majority = compute_majority(votes)
        majority_addresses, minority_addresses = who_is_in_vote_majority(
            votes, majority
        )

        # Ensure round_index is valid for appeals
        if (
            transaction_budget.appeals
            and round_index > 0
            and round_index - 1 <= len(transaction_budget.appeals)
        ):
            appeal_bond = compute_appeal_bond_partial(
                normal_round_index=round_index - 2,
                leader_timeout=transaction_budget.leaderTimeout,
                validators_timeout=transaction_budget.validatorsTimeout,
            )
            if majority == "UNDETERMINED":
                for addr in votes.keys():
                    if addr in fee_distribution.fees:
                        fee_distribution.fees[addr].validator_node += appeal_bond / len(
                            votes.keys()
                        ) + transaction_budget.validatorsTimeout
            else:
                # Distribute to majority validators
                for addr in majority_addresses:
                    if addr in fee_distribution.fees and majority_addresses:
                        fee_distribution.fees[
                            addr
                        ].validator_node += transaction_budget.validatorsTimeout
                        fee_distribution.fees[addr].validator_node += appeal_bond / len(
                            majority_addresses
                        )

                # Add penalty for minority validators
                for addr in minority_addresses:
                    if addr in fee_distribution.fees:
                        fee_distribution.fees[addr].validator_node -= (
                            penalty_reward_coefficient
                            * transaction_budget.validatorsTimeout
                        )

            first_addr = next(iter(votes.keys()), None)
            if first_addr and first_addr in fee_distribution.fees:
                fee_distribution.fees[
                    first_addr
                ].leader_node += transaction_budget.leaderTimeout

    elif label == "leader_timeout_50_previous_appeal_bond":
        sender_address = transaction_budget.senderAddress
        first_addr = next(iter(votes.keys()), None)

        # Ensure round_index is valid for appeals
        if (
            transaction_budget.appeals
            and round_index > 0
            and round_index - 1 <= len(transaction_budget.appeals)
        ):
            appeal_bond = transaction_budget.appeals[
                floor(round_index / 2) - 1
            ].appealBond

            if first_addr and first_addr in fee_distribution.fees:
                fee_distribution.fees[first_addr].leader_node += appeal_bond / 2

            if sender_address in fee_distribution.fees:
                fee_distribution.fees[sender_address].sender_node += appeal_bond / 2

    elif label == "leader_timeout_150_previous_normal_round":
        majority = compute_majority(votes)
        majority_addresses, minority_addresses = who_is_in_vote_majority(
            votes, majority
        )
        sender_address = transaction_budget.senderAddress
        first_addr = next(iter(votes.keys()), None)

        if first_addr and first_addr in fee_distribution.fees:
            fee_distribution.fees[first_addr].leader_node += (
                transaction_budget.leaderTimeout * 1.5
            )
        if sender_address in fee_distribution.fees:
            fee_distribution.fees[sender_address].sender_node += (
                transaction_budget.leaderTimeout / 2
            )

        # Distribute to majority validators
        for addr in majority_addresses:
            if addr in fee_distribution.fees and majority_addresses:
                fee_distribution.fees[
                    addr
                ].validator_node += transaction_budget.validatorsTimeout
                fee_distribution.fees[addr].validator_node += appeal_bond / len(
                    majority_addresses
                )

        # Add penalty for minority validators
        for addr in minority_addresses:
            if addr in fee_distribution.fees:
                fee_distribution.fees[addr].validator_node -= (
                    penalty_reward_coefficient * transaction_budget.validatorsTimeout
                )

    else:
        raise ValueError(f"Invalid label: {label}")

    return fee_distribution
