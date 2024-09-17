# simulation/models.py


class Validator:
    def __init__(self, id, own_stake):
        self.id = id
        self.own_stake = own_stake
        self.delegated_stake = 0
        self.total_stake = own_stake  # own_stake + delegated_stake
        self.history = [self.total_stake]

    def update_total_stake(self):
        self.total_stake = self.own_stake + self.delegated_stake


class Investor:
    def __init__(self, id, stake):
        self.id = id
        self.stake = stake
        self.delegated_validator = None
        self.history = [stake]

    def delegate(self, validator):
        self.delegated_validator = validator
        validator.delegated_stake += self.stake
        validator.update_total_stake()
