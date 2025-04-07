import re
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Literal, Union, Optional

# Ethereum address regex pattern
ETH_ADDRESS_REGEX = r"^0x[a-fA-F0-9]{40}$"

# Define vote types
VoteType = Literal["Agree", "Disagree", "Timeout"]
LeaderAction = Literal["LeaderReceipt", "LeaderTimeout"]
VoteValue = Union[VoteType, List[Union[LeaderAction, VoteType]]]

# Define round outcome types
MajorityOutcome = Literal["AGREE", "DISAGREE", "TIMEOUT", "UNDETERMINED"]
RoundLabel = Literal[
    "normal_round",
    "empty_round",
    "appeal_leader_timeout_unsuccessful",
    "appeal_leader_timeout_successful",
    "appeal_leader_successful",
    "appeal_leader_unsuccessful",
    "appeal_validator_successful",
    "appeal_validator_unsuccessful",
    "leader_timeout",
    "validators_penalty_only_round",
    "skip_round",
    "leader_timeout_50_percent",
    "split_previous_appeal_bond",
    "leader_timeout_50_previous_appeal_bond",
    "leader_timeout_150_previous_normal_round",
]


class Appeal(BaseModel):
    """
    Model for an appeal within a transaction.
    """

    appealantAddress: str

    @validator("appealantAddress")
    def validate_address(cls, v):
        if not re.match(ETH_ADDRESS_REGEX, v):
            raise ValueError(f"Invalid Ethereum address: {v}")
        return v


class Rotation(BaseModel):
    """
    A rotation is a collection of votes from different addresses.
    """

    votes: Dict[str, VoteValue]

    @validator("votes")
    def validate_addresses(cls, v):
        for addr in v.keys():
            if not re.match(ETH_ADDRESS_REGEX, addr):
                raise ValueError(f"Invalid Ethereum address: {addr}")
        return v


class Round(BaseModel):
    """
    A round consists of one or more rotations.
    """

    rotations: List[Rotation]


class TransactionRoundResults(BaseModel):
    """
    All rounds in a transaction.
    """

    rounds: List[Round]


class TransactionBudget(BaseModel):
    """
    Budget and parameters for a transaction.
    """

    leaderTimeout: int = Field(ge=0)
    validatorsTimeout: int = Field(ge=0)
    appealRounds: int = Field(ge=1)
    rotations: List[int]
    senderAddress: str
    appeals: Optional[List[Appeal]] = []

    @validator("senderAddress")
    def validate_sender_address(cls, v):
        if not re.match(ETH_ADDRESS_REGEX, v):
            raise ValueError(f"Invalid sender Ethereum address: {v}")
        return v

    @validator("rotations")
    def rotations_length_matches_appeal_rounds(cls, v, values):
        if "appealRounds" in values and len(v) != values["appealRounds"]:
            raise ValueError(
                f"Length of rotations ({len(v)}) must match appealRounds ({values['appealRounds']})"
            )
        return v


class FeeEntry(BaseModel):
    """
    Fee entry for an address, containing fees for different roles.
    """

    leader: int = Field(default=0, ge=0)
    leader_node: int = Field(default=0, ge=0)
    validator_node: int = Field(default=0, ge=0)
    sender: int = Field(default=0, ge=0)
    sender_node: int = Field(default=0, ge=0)
    appealant: int = Field(default=0, ge=0)
    appealant_node: int = Field(default=0, ge=0)


class FeeDistribution(BaseModel):
    """
    Distribution of fees across addresses.
    """

    fees: Dict[str, FeeEntry] = {}

    @validator("fees")
    def validate_fee_addresses(cls, v):
        for addr in v.keys():
            if not re.match(ETH_ADDRESS_REGEX, addr):
                raise ValueError(
                    f"Invalid Ethereum address in fee distribution: {addr}"
                )
        return v
