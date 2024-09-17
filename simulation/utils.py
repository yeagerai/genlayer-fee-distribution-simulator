# simulation/utils.py

import pandas as pd


def prepare_validator_data(validators):
    data = []
    for v in validators:
        for t, stake in enumerate(v.history):
            data.append(
                {"Transaction": t, "Stake": stake, "Validator": f"Validator {v.id}"}
            )
    return pd.DataFrame(data)


def prepare_investor_data(investors):
    data = []
    for inv in investors:
        for t, stake in enumerate(inv.history):
            data.append(
                {"Transaction": t, "Stake": stake, "Investor": f"Investor {inv.id}"}
            )
    return pd.DataFrame(data)
