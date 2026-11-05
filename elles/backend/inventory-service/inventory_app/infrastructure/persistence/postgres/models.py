from sqlalchemy import Column, String, Integer, DateTime, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()
class StockItemModel(Base):
    __tablename__ = "stock_item"

    sku = Column(String(100), primary_key=True, index=True)
    on_hand = Column(Integer, nullable=False, default=0)
    reserved = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

class StockMovementModel(Base):
    __tablename__ =  "stock_movements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(100), ForeignKey("stock_items.sku", ondelete="CASCADE"), nullable=False, index=True)
    delta_on_hand = Column(Integer, nullable=False)
    delta_reserved = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)