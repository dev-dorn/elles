"""Create the stock_items table with database-enforced quantity invariants.

Revision ID: 0002_stock_items
Revises: 0001_baseline
Create Date: 2026-11-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_stock_items"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stock_items",
        sa.Column("sku", sa.String(length=100), nullable=False),
        sa.Column("on_hand", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("reserved", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "on_hand >= 0",
            name="ck_stock_items_on_hand_nonnegative",
        ),
        sa.CheckConstraint(
            "reserved >= 0",
            name="ck_stock_items_reserved_nonnegative",
        ),
        sa.CheckConstraint(
            "reserved <= on_hand",
            name="ck_stock_items_reserved_lte_on_hand",
        ),
        sa.PrimaryKeyConstraint("sku", name="pk_stock_items"),
    )


def downgrade() -> None:
    op.drop_table("stock_items")
