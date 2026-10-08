class DomainException(Exception):
    """ Base exception for all domain rule violations"""
    pass

class InvalidProductStateError(DomainException):
    """Raised when a business rule is violated """
    pass