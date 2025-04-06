import pytest
from datetime import datetime
from decimal import Decimal
from app.stock_exchange import place_order, OrderPlacementError
from app.types import Order, OrderType, OrderSide
import app.stock_exchange as se

def test_place_order_success():
    order = Order(
        id="1",
        created_at=datetime.utcnow(),
        type=OrderType.MARKET ,
        side=OrderSide.BUY,
        instrument="TEST12345678",
        quantity=10,
        status="pending"
    )
    se.random.random = lambda: 0.2
    place_order(order)

def test_place_order_failure():
    with pytest.raises(OrderPlacementError):
        se.random.random = lambda: 1.0
        
        order = Order(
            id="2",
            created_at=datetime.utcnow(),
            type=OrderType.MARKET,
            side=OrderSide.BUY,
            instrument="TEST12345678",
            quantity=10,
            status="pending"
        )
        place_order(order)