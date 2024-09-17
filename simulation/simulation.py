# simulation/simulation.py

import random
import numpy as np
from .models import Validator, Investor


def initialize_validators(N_validators, min_stake, max_stake):
    validators = []
    for i in range(N_validators):
        own_stake = random.uniform(min_stake, max_stake)
        validators.append(Validator(id=i, own_stake=own_stake))
    return validators


def initialize_investors(N_investors, min_stake, max_stake):
    investors = []
    for i in range(N_investors):
        stake = random.uniform(min_stake, max_stake)
        investors.append(Investor(id=i, stake=stake))
    return investors


def calculate_selection_probabilities(validators, method="proportional"):
    stakes = np.array([max(0, v.total_stake) for v in validators])
    total_stakes = stakes.sum()
    if total_stakes <= 0:
        probabilities = np.ones(len(validators)) / len(validators)
    else:
        if method == "proportional":
            probabilities = stakes / total_stakes
        elif method == "logarithmic":
            log_stakes = np.log(stakes + 1)
            probabilities = log_stakes / log_stakes.sum()
    return probabilities


def initial_delegation(investors, validators):
    for investor in investors:
        chosen_validator = random.choice(validators)
        investor.delegate(chosen_validator)


def redistribute_stakes(investors, validators):
    validator_returns = []
    for v in validators:
        if len(v.history) > 1:
            validator_returns.append(v.history[-1] - v.history[-2])
        else:
            validator_returns.append(v.total_stake)

    total_returns = sum(validator_returns)
    if total_returns == 0:
        expected_returns = [v.total_stake for v in validators]
    else:
        expected_returns = validator_returns

    total_weights = sum(expected_returns)
    if total_weights == 0:
        weights = np.ones(len(validators)) / len(validators)
    else:
        weights = [max(0, r) / total_weights for r in expected_returns]

    for investor in investors:
        if investor.delegated_validator:
            previous_validator = investor.delegated_validator
            previous_validator.delegated_stake -= investor.stake
            previous_validator.delegated_stake = max(
                0, previous_validator.delegated_stake
            )
            previous_validator.update_total_stake()

        chosen_validator = random.choices(validators, weights=weights, k=1)[0]
        investor.delegate(chosen_validator)


def simulate_transactions(
    validators, investors, num_transactions, reward, method="proportional"
):
    N = len(validators)
    for tx_num in range(num_transactions):
        if tx_num > 0:
            redistribute_stakes(investors, validators)

        for v in validators:
            v.update_total_stake()

        probabilities = calculate_selection_probabilities(validators, method)

        selected_indices = np.random.choice(N, size=5, replace=False, p=probabilities)
        selected_validators = [validators[i] for i in selected_indices]

        reward_per_validator = reward / 5
        for v in selected_validators:
            validator_reward = reward_per_validator * 0.1  # Validator keeps 10%
            delegator_reward = reward_per_validator * 0.9  # Delegators get 90%
            v.own_stake += validator_reward

            total_delegated_stake = v.delegated_stake if v.delegated_stake > 0 else 1
            for investor in investors:
                if investor.delegated_validator == v:
                    share = investor.stake / total_delegated_stake
                    investor.stake += delegator_reward * share
                    investor.stake = max(0, investor.stake)
                    investor.history.append(investor.stake)
            v.update_total_stake()
            v.own_stake = max(0, v.own_stake)
            v.delegated_stake = max(0, v.delegated_stake)
            v.total_stake = max(0, v.total_stake)
            v.history.append(v.total_stake)

        for v in validators:
            if v not in selected_validators:
                v.history.append(v.total_stake)
        for investor in investors:
            if investor.delegated_validator not in selected_validators:
                investor.history.append(investor.stake)
