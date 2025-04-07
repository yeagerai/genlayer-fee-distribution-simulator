from typing import Dict, List, Any
from custom_types import VoteType, VoteValue, MajorityOutcome


def normalize_vote(vote_value: VoteValue) -> VoteType:
    """
    Convert any vote value to a standard VoteType for comparison.

    Args:
        vote_value: A vote value which could be a simple VoteType or a list with LeaderAction

    Returns:
        The normalized VoteType
    """
    if isinstance(vote_value, list):
        # For leader votes like ["LeaderReceipt", "Agree"], use the second value
        return vote_value[1]
    return vote_value


def who_is_in_majority(
    rotation: Dict[str, VoteValue], majority: MajorityOutcome
) -> List[str]:
    """
    Return the addresses that are in majority.

    Args:
        rotation: A dictionary mapping addresses to votes
        majority: The majority outcome to match against

    Returns:
        A list of addresses that contributed to the majority
    """
    majority_addresses = []

    # Map MajorityOutcome to the corresponding VoteType for comparison
    vote_mapping = {
        "AGREE": "Agree",
        "DISAGREE": "Disagree",
        "TIMEOUT": "Timeout",
        "UNDETERMINED": None,  # Special case handled below
    }

    # If majority is UNDETERMINED, collect addresses with Disagree votes
    if majority == "UNDETERMINED":
        for addr, vote in rotation.items():
            if normalize_vote(vote) == "Disagree":
                majority_addresses.append(addr)
    # Otherwise, find all addresses with votes matching the majority
    elif vote_mapping[majority] is not None:
        target_vote = vote_mapping[majority]
        for addr, vote in rotation.items():
            if normalize_vote(vote) == target_vote:
                majority_addresses.append(addr)

    minority_addresses = list(set(rotation.keys()) - set(majority_addresses))
    return majority_addresses, minority_addresses


def compute_majority(rotation: Dict[str, VoteValue]) -> MajorityOutcome:
    """
    Calculate the majority vote result.

    Args:
        rotation: A dictionary mapping addresses to votes

    Returns:
        The majority outcome as a MajorityOutcome type
    """
    # Empty rotation case
    if not rotation:
        return "UNDETERMINED"

    # Normalize votes for counting
    normalized_votes = {addr: normalize_vote(vote) for addr, vote in rotation.items()}

    # Count each type of vote
    vote_counts = {"Agree": 0, "Disagree": 0, "Timeout": 0, "Idle": 0}
    for vote in normalized_votes.values():
        if vote in vote_counts:
            vote_counts[vote] += 1

    total_votes = len(rotation)
    majority_threshold = (total_votes // 2) + 1

    # Determine majority based on vote counts
    if vote_counts.get("Disagree", 0) >= majority_threshold:
        return "UNDETERMINED"  # Disagreement
    elif vote_counts.get("Agree", 0) >= majority_threshold:
        return "AGREE"  # Accept
    elif vote_counts.get("Timeout", 0) >= majority_threshold:
        return "TIMEOUT"  # Timeout
    else:
        return "UNDETERMINED"  # No clear majority
