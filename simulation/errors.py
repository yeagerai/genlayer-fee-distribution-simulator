class OutOfGasError(Exception):
    """Raised when transaction budget is depleted"""

    pass


class FinalityError(Exception):
    """Raised when trying to appeal a round after finality window period"""

    pass
