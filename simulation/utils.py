# simulation/utils.py
import random

import numpy as np

import streamlit.components.v1 as components


def mermaid(code: str) -> None:
    components.html(
        f"""
        <pre class="mermaid">
            {code}
        </pre>

        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true }});
        </script>
        """
    )


def set_random_seed(seed_value):
    random.seed(seed_value)
    np.random.seed(seed_value)


def generate_ethereum_address():
    """Generates a random 40-character hex string to simulate an Ethereum address."""
    address = "0x" + "".join(random.choices("0123456789abcdef", k=40))
    return address


def generate_mermaid_flowchart(transaction_path):
    """Generates a Mermaid flowchart from the transaction path."""
    mermaid_code = "graph TD\n"
    node_counter = 0
    node_dict = {}
    previous_node = None
    for step in transaction_path:
        node_label = step.replace('"', "").replace("[", "(").replace("]", ")")
        node_name = f"node{node_counter}"
        node_dict[step] = node_name
        mermaid_code += f'{node_name}["{node_label}"]\n'
        if previous_node is not None:
            mermaid_code += f"{previous_node} --> {node_name}\n"
        previous_node = node_name
        node_counter += 1
    return mermaid_code
