import re
from pydantic import (
    BaseModel,
    Field,
    validator,
    field_validator,
    ConfigDict,
    model_validator,
)
from typing import Dict, List, Literal, Union, Optional

# Ethereum address regex pattern
ETH_ADDRESS_REGEX = r"^0x[a-fA-F0-9]{40}$"

# Define vote types
VoteType = Literal["Agree", "Disagree", "Timeout", "Idle", "NA"]
LeaderAction = Literal["LeaderReceipt", "LeaderTimeout"]
VoteValue = Union[
    VoteType,  # e.g., "Agree", "Disagree", "Timeout", "Idle"
    List[Union[LeaderAction, VoteType]],  # e.g., ["LeaderReceipt", "Agree"]
    List[
        Union[LeaderAction, VoteType, str]
    ],  # e.g., ["LeaderReceipt", "Agree", "0x123"]
    List[Union[VoteType, str]],  # e.g., ["Disagree", "0x123"]
]

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

    @field_validator("appealantAddress")
    def validate_address(cls, v):
        if not re.match(ETH_ADDRESS_REGEX, v):
            raise ValueError(f"Invalid Ethereum address: {v}")
        return v


class Rotation(BaseModel):
    """
    A rotation is a collection of votes from different addresses.
    """

    votes: Dict[str, VoteValue]
    reserve_votes: Dict[str, VoteValue] = {}

    @field_validator("votes")
    def validate_vote_addresses(cls, v):
        for addr in v.keys():
            if not re.match(ETH_ADDRESS_REGEX, addr):
                raise ValueError(f"Invalid Ethereum address: {addr}")
        return v

    @field_validator("reserve_votes")
    def validate_reserve_addresses(cls, v):
        for addr in v.keys():
            if not re.match(ETH_ADDRESS_REGEX, addr):
                raise ValueError(f"Invalid reserve Ethereum address: {addr}")
        return v

    @field_validator("votes")
    def validate_vote_hashes(cls, v):
        for addr, vote in v.items():
            if isinstance(vote, list) and len(vote) > 1:
                # Check if last element is a hash
                if len(vote) == 3 or (
                    len(vote) == 2 and vote[0] not in ["LeaderReceipt", "LeaderTimeout"]
                ):
                    hash_value = vote[-1]
                    if not re.match(r"^0x[a-fA-F0-9]+$", hash_value):
                        raise ValueError(
                            f"Invalid hash format for address {addr}: {hash_value}"
                        )
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


class FeeEntry(BaseModel):
    """
    Fee entry for an address, containing fees for different roles.
    """

    leader_node: int = Field(default=0, ge=0)
    validator_node: int = Field(default=0, ge=0)
    sender_node: int = Field(default=0, ge=0)
    appealant_node: int = Field(default=0, ge=0)
    stake: float = Field(default=0, ge=0)


class FeeDistribution(BaseModel):
    """
    Distribution of fees across addresses.
    """

    fees: Dict[str, FeeEntry] = {}

    @field_validator("fees")
    def validate_fee_addresses(cls, v):
        for addr in v.keys():
            if not re.match(ETH_ADDRESS_REGEX, addr):
                raise ValueError(
                    f"Invalid Ethereum address in fee distribution: {addr}"
                )
        return v


class TransactionBudget(BaseModel):
    """
    Budget and parameters for a transaction.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    leaderTimeout: int = Field(ge=0)
    validatorsTimeout: int = Field(ge=0)
    appealRounds: int = Field(ge=0)
    rotations: List[int]
    senderAddress: str
    appeals: Optional[List[Appeal]] = []
    staking_distribution: Literal["constant", "normal"] = Field(default="constant")
    staking_mean: Optional[float] = Field(default=None, ge=0)
    staking_variance: Optional[float] = Field(default=None, ge=0)

    @field_validator("senderAddress")
    def validate_sender_address(cls, v):
        if not re.match(ETH_ADDRESS_REGEX, v):
            raise ValueError(f"Invalid sender Ethereum address: {v}")
        return v

    @model_validator(mode="after")
    def validate_rotations(self):
        if len(self.rotations) != self.appealRounds + 1:
            raise ValueError("Number of rotations must match appealRounds")
        return self

    @model_validator(mode="after")
    def validate_staking_params(self):
        if self.staking_distribution == "normal":
            if self.staking_mean is None or self.staking_variance is None:
                raise ValueError(
                    "staking_mean and staking_variance must be provided for normal distribution"
                )
        if self.staking_distribution == "constant" and (
            self.staking_mean is not None or self.staking_variance is not None
        ):
            raise ValueError(
                "staking_mean and staking_variance should not be provided for constant distribution"
            )
        return self
