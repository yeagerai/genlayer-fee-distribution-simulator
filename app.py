# app.py

# TODO: WIP, this file currently does not work!!!

import random

import altair as alt
import pandas as pd
import streamlit as st

from simulation.config_constants import (
    VOTE_AGREE,
    VOTE_DISAGREE,
    VOTE_IDLE,
    VOTE_TIMEOUT,
)
from simulation.simulation import TransactionSimulator
from simulation.fee_mechanism import fee_structure
from simulation.validator_selection import generate_validators_pool
from simulation.models import Validator
from simulation.utils import mermaid


def main():
    st.title("GenLayer Protocol Simulation")

    # Create tabs
    tab1, tab2 = st.tabs(
        ["Transaction Simulation", "Validator Stake Evolution", "Test Suite"]
    )

    with tab1:
        transaction_simulation_tab()

    with tab2:
        stake_evolution_tab()


def transaction_simulation_tab():
    st.header("Transaction Simulation")

    # Fee Parameter Inputs
    st.subheader("Adjust Fee Structure")
    leader_units = st.number_input(
        "Leader Units (LU)", value=float(fee_structure["LU"]), min_value=0.0
    )
    validator_units = st.number_input(
        "Validator Units (VU)", value=float(fee_structure["VU"]), min_value=0.0
    )
    leader_idle_penalty = st.number_input(
        "Leader Idle Penalty",
        value=float(fee_structure["leader_idle_penalty"]),
        min_value=0.0,
    )
    leader_timeout_penalty = st.number_input(
        "Leader Timeout Penalty",
        value=float(fee_structure["leader_timeout_penalty"]),
        min_value=0.0,
    )
    validator_violation_penalty = st.number_input(
        "Validator Violation Penalty",
        value=float(fee_structure["validator_violation_penalty"]),
        min_value=0.0,
    )
    validator_idle_penalty = st.number_input(
        "Validator Idle Penalty",
        value=float(fee_structure["validator_idle_penalty"]),
        min_value=0.0,
    )

    # Update fee structure
    custom_fee_structure = {
        "LU": leader_units,
        "VU": validator_units,
        "leader_idle_penalty": leader_idle_penalty,
        "leader_timeout_penalty": leader_timeout_penalty,
        "validator_violation_penalty": validator_violation_penalty,
        "validator_idle_penalty": validator_idle_penalty,
    }

    # Transaction Simulation Controls
    st.subheader("Transaction Parameters")
    leader_decision = st.selectbox(
        "Leader Decision",
        [VOTE_AGREE, VOTE_DISAGREE, VOTE_IDLE, VOTE_TIMEOUT],
        format_func=lambda x: {
            VOTE_AGREE: "Agree (A)",
            VOTE_DISAGREE: "Disagree (D)",
            VOTE_IDLE: "Idle (I)",
            VOTE_TIMEOUT: "Timeout (T)",
        }[x],
        index=0,
    )
    appeal = st.checkbox("Enable Appeal", value=True)
    round_number = st.number_input("Round Number (r)", min_value=0, value=0, step=1)

    # Simulate Button
    if st.button("Simulate Transaction"):
        # Run the simulation
        all_validators = generate_validators_pool()
        simulator = TransactionSimulator(
            all_validators=all_validators,
            r=round_number,
            leader_decision=leader_decision,
            appeal=appeal,
            fee_structure=custom_fee_structure,
        )
        simulator.run_simulation()

        # Display Output
        st.subheader("Transaction Path")
        for step in simulator.transaction_path:
            st.write(step)

        st.subheader("Final Fee Distribution")
        total_fees = []
        leader_total = simulator.leader.rewards - simulator.leader.penalties
        total_fees.append(
            f"Leader (Validator {simulator.leader.id}) net fee: {leader_total} "
            f"(Rewards: {simulator.leader.rewards}, Penalties: {simulator.leader.penalties})"
        )
        for validator in simulator.validators:
            validator_total = validator.rewards - validator.penalties
            total_fees.append(
                f"Validator {validator.id} net fee: {validator_total} "
                f"(Rewards: {validator.rewards}, Penalties: {validator.penalties})"
            )
        for fee in total_fees:
            st.write(fee)

        # Display the Mermaid graph
        st.subheader("Transaction Flowchart")
        mermaid_code = simulator.generate_mermaid_code()
        print(mermaid_code)
        mermaid(mermaid_code)


def stake_evolution_tab():
    st.header("Validator Stake Evolution")

    # Simulation Settings
    st.subheader("Simulation Settings")
    num_transactions = st.number_input(
        "Number of Transactions", min_value=1, value=100, step=1
    )
    initial_total_supply = st.number_input(
        "Total Supply", min_value=1.0, value=42000000000.0
    )
    validator_count = st.number_input(
        "Number of Validators", min_value=1, value=1000, step=1
    )

    # Optionally, allow adjusting initial stakes distribution
    stake_distribution = st.selectbox(
        "Stake Distribution", ["Dirichlet (Default)", "Uniform"]
    )

    # Run Batch Simulation Button
    if st.button("Run Batch Simulation"):
        # Initialize validators
        if stake_distribution == "Dirichlet (Default)":
            all_validators = generate_validators_pool(
                N=int(validator_count), total_supply=initial_total_supply
            )
        else:
            # Implement uniform stake distribution if needed
            pass

        # Initialize validators_list
        validators_list = [Validator(id=val[0], stake=val[1]) for val in all_validators]

        # Data structure to store stakes over time
        stake_history = pd.DataFrame()

        # Simulate multiple transactions
        for tx in range(int(num_transactions)):
            # Run a transaction simulation
            simulator = TransactionSimulator(
                all_validators=all_validators,
                r=0,  # Adjust as needed
                leader_decision=VOTE_AGREE,  # Or randomize
                appeal=True,
                fee_structure=fee_structure,  # Use default or allow customization
                validators_list=validators_list,  # Pass the existing validators_list
            )
            simulator.run_simulation()

            # Record stakes at this point
            stakes = {validator.id: validator.stake for validator in validators_list}
            stakes["transaction"] = tx
            stake_history = stake_history.append(stakes, ignore_index=True)

        # Melt the DataFrame for Altair plotting
        stake_history_melted = stake_history.melt(
            id_vars=["transaction"], var_name="validator", value_name="stake"
        )

        # Sample a subset of validators for plotting
        sample_size = min(20, len(all_validators))
        sampled_validator_ids = random.sample(
            [val[0] for val in all_validators], sample_size
        )
        stake_history_sampled = stake_history_melted[
            stake_history_melted["validator"].isin(sampled_validator_ids)
        ]

        # Plot with Altair
        st.subheader("Stake Evolution Over Time")
        chart = (
            alt.Chart(stake_history_sampled)
            .mark_line()
            .encode(
                x="transaction:Q",
                y="stake:Q",
                color="validator:N",
                tooltip=["validator:N", "stake:Q"],
            )
            .interactive()
        )

        st.altair_chart(chart, use_container_width=True)

        # Display final stakes
        st.subheader("Final Validator Stakes")
        final_stakes = stake_history.iloc[-1].drop("transaction")
        final_stakes_df = final_stakes.to_frame(name="Stake").reset_index()
        final_stakes_df = final_stakes_df.rename(columns={"index": "Validator ID"})
        st.dataframe(final_stakes_df)


if __name__ == "__main__":
    main()
