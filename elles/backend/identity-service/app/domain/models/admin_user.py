from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

class UserRole  (str, Enum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"

@dataclass
class AdminUser:
    """ Aggregate  root : Represents an admin user who can manage the store """
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    password_hash: str = ""
    full_name: str = ""
    role: UserRole = UserRole.ADMIN
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: datetime | None = None

    def update_last_login(self):
        """ Records the last login date """
        self.last_login = datetime.now(timezone.utc)

    def deactivate(self):
        """Soft-delete the admin user"""
        self.is_active = False
        

    def activate(self):
        """ Reactivate a deactivated admin user"""
        self.is_active = True

