class DomainException(Exception):
    """ Base exception for all exceptions """
    pass
class InvalidCredentialsError(DomainException):
    """Raised when the credentials are invalid"""
    pass
class InactiveAccountError(DomainException):
    """Raised when the account is inactive"""
    pass
class EmailAlreadyExistsError(DomainException):
    """Raised when the email already exists"""
    pass
