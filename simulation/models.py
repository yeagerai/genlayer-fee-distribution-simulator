# simulation/models.py
import random
from simulation.constants import (
    VOTE_AGREE,
    VOTE_DISAGREE,
    VOTE_IDLE,
    VOTE_TIMEOUT,
    VOTE_VIOLATION,
)


class Validator:
    def __init__(self, id, stake, prob_agree=0.7, prob_random_scenario=0.05):
        self.id = id
        self.stake = stake
        self.prob_agree = prob_agree
        self.prob_random_scenario = prob_random_scenario
        self.fee_earned = 0
        self.penalties = 0
        self.rewards = 0

    def vote(self):
        """Simulate the validator's vote based on probabilities."""
        rand = random.random()
        if rand < self.prob_random_scenario:
            return random.choice(
                [VOTE_AGREE, VOTE_DISAGREE, VOTE_TIMEOUT, VOTE_IDLE, VOTE_VIOLATION]
            )
        if rand < self.prob_agree:
            return VOTE_AGREE
        else:
            return VOTE_DISAGREE


class Leader(Validator):
    def __init__(self, id, stake, decision=None, prob_blocking=0.01):
        super().__init__(id, stake)
        self.vote_value = None
        self.prob_blocking = prob_blocking
        if not decision:
            self.decision = (
                VOTE_AGREE
                if random.random() > self.prob_blocking
                else random.choice([VOTE_TIMEOUT, VOTE_IDLE])
            )
        else:
            self.decision = decision
