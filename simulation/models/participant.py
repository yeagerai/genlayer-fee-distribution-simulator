# simulation/models/participant.py

from dataclasses import dataclass
from simulation.utils import generate_ethereum_address
from simulation.models.enums import Role

@dataclass
class RoundData:
    id: str
    role: Role
    reward: int

class Participant:
    def __init__(self, id: str | None = None):
        self.id = id if id else generate_ethereum_address()
        self.rounds: list[RoundData] = []
        
    def add_to_round(self, round_id: str, role: Role) -> None:
        self.rounds.append(RoundData(round_id, role, 0))

    def get_total_rewards(self) -> int:
        return sum(round.reward for round in self.rounds)
        
    def get_role_in_round(self, round_id: str) -> Role | None:
        return next((round.role for round in self.rounds if round.id == round_id), None)

    def __repr__(self) -> str:
        return f"Participant(id={self.id}, rounds={len(self.rounds)}, total_rewards={self.get_total_rewards()})"
