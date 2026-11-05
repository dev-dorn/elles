"""Empty baseline for inventory database migrations.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-11-05
"""

from typing import Sequence, Union

revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Register the baseline; inventory tables are added by later revisions."""
    pass


def downgrade() -> None:
    """Remove the baseline revision without dropping application tables."""
    pass
