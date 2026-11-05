from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class StockItemModel(Base):
    __tablename__ = "stock_items"
    __table_args__ = (
        CheckConstraint("on_hand >= 0", name="ck_stock_items_on_hand_nonnegative"),
        CheckConstraint("reserved >= 0", name="ck_stock_items_reserved_nonnegative"),
        CheckConstraint("reserved <= on_hand", name="ck_stock_items_reserved_lte_on_hand"),
    )

    sku = Column(String(100), primary_key=True)
    on_hand = Column(Integer, nullable=False, default=0, server_default=text("0"))
    reserved = Column(Integer, nullable=False, default=0, server_default=text("0"))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class StockMovementModel(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(
        String(100),
        ForeignKey("stock_items.sku", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delta_on_hand = Column(Integer, nullable=False)
    delta_reserved = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
