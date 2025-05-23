from typing import List
from fee_simulator.models import TransactionRoundResults
from fee_simulator.types import RoundLabel
from fee_simulator.core.majority import compute_majority


def label_rounds(transaction_results: TransactionRoundResults) -> List[RoundLabel]:
    # Extract rounds for processing
    rounds = []
    for i, round_obj in enumerate(transaction_results.rounds):
        # Get the last rotation's votes from each round or empty dict if no rotations
        if round_obj.rotations:
            rounds.append(round_obj.rotations[-1].votes)
        else:
            rounds.append({})

    leader_addresses = []
    for i, round in enumerate(rounds):
        leader_addresses.append(next(iter(round.keys())))
    labels = ["NORMAL_ROUND"]
    if rounds[0][leader_addresses[0]] == ["LEADER_TIMEOUT", "NA"]:
        labels = ["LEADER_TIMEOUT"]
        if len(rounds) == 1:
            labels = ["LEADER_TIMEOUT_50_PERCENT"]
            return labels

    for i, round in enumerate(rounds):
        if i == 0:
            continue
        if len(round) == 0:
            labels.append("EMPTY_ROUND")
        if i % 2 == 1:
            if (
                rounds[i - 1][leader_addresses[i - 1]] == ["LEADER_TIMEOUT", "NA"]
                and i + 1 < len(rounds)
                and rounds[i + 1][leader_addresses[i + 1]] == ["LEADER_TIMEOUT", "NA"]
            ):
                labels.append("APPEAL_LEADER_TIMEOUT_UNSUCCESSFUL")
                continue
            if (
                rounds[i - 1][leader_addresses[i - 1]] == ["LEADER_TIMEOUT", "NA"]
                and i + 1 < len(rounds)
                and rounds[i + 1][leader_addresses[i + 1]][0] == "LEADER_RECEIPT"
            ):
                labels.append("APPEAL_LEADER_TIMEOUT_SUCCESSFUL")
                continue
            if (
                compute_majority(rounds[i - 1]) in ["UNDETERMINED", "DISAGREE"]
                and i + 1 < len(rounds)
                and compute_majority(rounds[i + 1]) not in ["UNDETERMINED", "DISAGREE"]
            ):
                labels.append("APPEAL_LEADER_SUCCESSFUL")
                continue
            if (
                compute_majority(rounds[i - 1]) in ["UNDETERMINED", "DISAGREE"]
                and i + 1 < len(rounds)
                and compute_majority(rounds[i + 1]) in ["UNDETERMINED", "DISAGREE"]
            ):
                labels.append("APPEAL_LEADER_UNSUCCESSFUL")
                continue

            empty_candidate = i - 1
            while (
                empty_candidate >= 0
                and rounds[empty_candidate] == "EMPTY_ROUND"
                and compute_majority(rounds[empty_candidate])
                not in [
                    "UNDETERMINED",
                    "DISAGREE",
                ]
            ):
                empty_candidate -= 2
            if compute_majority(rounds[empty_candidate]) not in [
                "UNDETERMINED",
                "DISAGREE",
            ]:
                if empty_candidate >= 0 and compute_majority(round) != compute_majority(
                    rounds[empty_candidate]
                ):
                    labels.append("APPEAL_VALIDATOR_SUCCESSFUL")
                    continue
                else:
                    labels.append("APPEAL_VALIDATOR_UNSUCCESSFUL")
                    continue
        else:
            if rounds[i][leader_addresses[i]] == ["LEADER_TIMEOUT", "NA"]:
                labels.append("LEADER_TIMEOUT")
                continue
            else:
                labels.append("NORMAL_ROUND")
                continue
    # Handle special cases with the reversed list
    reverse_labels = labels[::-1]
    reverse_rounds = rounds[::-1]

    for i in range(len(reverse_rounds)):
        if i + 2 < len(reverse_rounds):
            if (
                reverse_labels[i] == "NORMAL_ROUND"
                and i + 1 < len(reverse_labels)
                and "APPEAL_LEADER_TIMEOUT_SUCCESSFUL" == reverse_labels[i + 1]
                and i + 2 < len(reverse_labels)
                and reverse_labels[i + 2] == "LEADER_TIMEOUT"
            ):
                reverse_labels[i] = "LEADER_TIMEOUT_150_PREVIOUS_NORMAL_ROUND"
                reverse_labels[i + 2] = "SKIP_ROUND"
                continue
            if (
                reverse_labels[i] == "NORMAL_ROUND"
                and i + 1 < len(reverse_labels)
                and "APPEAL" in reverse_labels[i + 1]
                and i + 2 < len(reverse_rounds)
                and compute_majority(reverse_rounds[i + 2])
                in [
                    "UNDETERMINED",
                    "DISAGREE",
                ]
            ):
                if "UNSUCCESSFUL" in reverse_labels[i + 1]:
                    reverse_labels[i] = "SPLIT_PREVIOUS_APPEAL_BOND"
                    continue
                else:
                    reverse_labels[i + 2] = "SKIP_ROUND"
                    continue

            if (
                i < len(labels)
                and labels[i] == "LEADER_TIMEOUT"
                and i + 1 < len(labels)
                and labels[i + 1] == "APPEAL_LEADER_TIMEOUT_UNSUCCESSFUL"
                and i + 2 < len(labels)
                and labels[i + 2] == "LEADER_TIMEOUT"
            ):
                reverse_labels[i] = "LEADER_TIMEOUT_50_PREVIOUS_APPEAL_BOND"
                reverse_labels[i + 2] = "LEADER_TIMEOUT_50_PERCENT"
                continue
        if i + 1 < len(reverse_labels):
            if (
                reverse_labels[i] == "APPEAL_VALIDATOR_SUCCESSFUL"
                and reverse_labels[i - 1] == "NORMAL_ROUND"
            ):
                reverse_labels[i + 1] = "SKIP_ROUND"
                continue

    labels = reverse_labels[::-1]
    return labels
