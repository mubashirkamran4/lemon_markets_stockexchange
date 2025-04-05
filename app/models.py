from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from app.types import OrderSide, OrderType

Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), nullable=False,server_default=func.now())
    type = Column(Enum(OrderType, name="order_type", 
                  values_callable=lambda x: [e.value for e in OrderType]),
                 nullable=False)
    side = Column(Enum(OrderSide, name="order_side",
                  values_callable=lambda x: [e.value for e in OrderSide]),
                 nullable=False)
    instrument = Column(String(12), nullable=False)
    limit_price = Column(Numeric(10, 2), nullable=True)
    quantity = Column(Integer, nullable=False)
    status = Column(Enum('pending', 'completed', 'failed', 'error', name='order_status'), nullable=False, server_default='pending')
    error_message = Column(Text, nullable=True)