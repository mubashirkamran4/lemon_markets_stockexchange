import pytest
from fastapi import status

def test_create_market_order_success(client):
    response = client.post(
        "/orders",
        json={
            "type": "market",
            "side": "buy",
            "instrument": "TEST12345678",
            "quantity": 10
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in response.json()

def test_create_limit_order_without_price(client):
    response = client.post(
        "/orders",
        json={
            "type": "limit",
            "side": "buy",
            "instrument": "TEST12345678",
            "quantity": 10
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Limit orders require limit_price" in str(response.content)