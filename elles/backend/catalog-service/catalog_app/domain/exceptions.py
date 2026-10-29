class DomainException(Exception):
    """ Base exception for all domain rule violations"""
    pass

class InvalidPriceError(DomainException):
    """Raised when a business rule is violated """
    pass
class DuplicateProductError(DomainException):
    """A product wit this slug, or one of its skus , already exists"""

