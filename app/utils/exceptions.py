class AppError(Exception):
    """Base class for errors that should be shown to the user as a friendly Uzbek message."""

    def __init__(self, user_message: str):
        self.user_message = user_message
        super().__init__(user_message)


class InvalidAmountError(AppError):
    pass


class CategoryInUseError(AppError):
    pass


class NotFoundError(AppError):
    pass
