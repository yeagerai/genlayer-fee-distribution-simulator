from fee_simulator.constants import ROUND_SIZES
from fee_simulator.core.majority import compute_majority


# TODO: todos contra todos
def get_validators_vote_configs(num_validators, majority):
    majority_threshold = (num_validators // 2) + 1
    if majority == "AGREE":
        return ["AGREE"] * majority_threshold + ["DISAGREE"] * (
            num_validators - majority_threshold
        )
    elif majority == "DISAGREE":
        return ["DISAGREE"] * majority_threshold + ["AGREE"] * (
            num_validators - majority_threshold
        )
    elif majority == "TIMEOUT":
        return ["TIMEOUT"] * majority_threshold + ["AGREE"] * (
            num_validators - majority_threshold
        )
    elif majority == "UNDETERMINED":
        return (
            ["AGREE"] * (num_validators // 3)
            + ["TIMEOUT"] * (num_validators // 3)
            + ["DISAGREE"] * (num_validators - 2 * num_validators // 3)
        )


def get_full_vote_configs(num_validators, majority):
    return ["LEADER_RECEIPT", "AGREE"] + get_validators_vote_configs(
        num_validators - 1, majority
    )


def get_leader_timeout_vote_configs(num_validators):
    return ["LEADER_TIMEOUT", "NA"] + ["NA"] * (num_validators - 1)


def get_leader_appeal_vote_configs(num_validators):
    return ["NA"] * (num_validators)


def generate_rounds(num_rounds):
    base_round_types = ["RECEIPT", "TIMEOUT"]
    possible_majorities = ["AGREE", "DISAGREE", "TIMEOUT", "UNDETERMINED"]
    appeal_types = ["LEADER_APPEAL", "VALIDATOR_APPEAL"]
    all_possible_transactions = []
    is_appeal_round = False
    for round_index in range(num_rounds):
        transaction_to_append = []
        if round_index % 2 == 1:
            is_appeal_round = True
        num_validators = ROUND_SIZES[round_index]

        if is_appeal_round:
            for appeal_type in appeal_types:
                if appeal_type == "LEADER_APPEAL":
                    transaction_to_append.append(
                        get_leader_appeal_vote_configs(num_validators)
                    )
                else:
                    for majority in possible_majorities:
                        transaction_to_append.append(
                            get_validators_vote_configs(num_validators, majority)
                        )
                        if majority != compute_majority(
                            transaction_to_append[-1]
                        ):  # if new majority is different than previous majority -> next round, else it finishes there
                            ...
                        else:
                            ...
        else:
            for base_round_type in base_round_types:
                if base_round_type == "RECEIPT":
                    for majority in possible_majorities:
                        transaction_to_append.append(
                            get_full_vote_configs(num_validators, majority)
                        )
                else:
                    transaction_to_append.append(
                        get_leader_timeout_vote_configs(num_validators)
                    )
            all_possible_transactions.append(transaction_to_append)

    return all_possible_transactions


# example of a transaction
# [
#     [
#         ["LEADER_RECEIPT", "AGREE", "AGREE", "AGREE", "AGREE"], # 5 normal round
#         ["DISAGREE","DISAGREE","DISAGREE", "DISAGREE", "DISAGREE", "AGREE", "AGREE"], # 7 and is a successful validator appeal round
#         ["LEADER_RECEIPT", "AGREE", "AGREE", "AGREE", "AGREE", "AGREE", "AGREE", "AGREE", "AGREE", "AGREE", "AGREE"], # 11 normal round
#     ]
# ]
