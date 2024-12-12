# simulation/models/participant.py

from simulation.utils import generate_ethereum_address
from simulation.models.enums import Role


class Participant:
    def __init__(self, id: str | None = None, role: Role | None = None):
        if id:
            self.id = id
        else:
            self.id = generate_ethereum_address()
        self.roles: dict[str, Role] = (
            {}
        )  # str is the id of round | appeal and Role is 'leader', 'validator', or 'appealant' in each round | appeal
        self.rewards: dict[str, int] = (
            {}
        )  # str is the id of round | appeal, and int is the reward obtained from that round, can be positive or negative
