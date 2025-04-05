from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field, condecimal, conint, constr, root_validator
from sqlalchemy.orm import Session
import logging

from app.types import Order as PydanticOrder, OrderSide, OrderType
from app.stock_exchange import place_order, OrderPlacementError
from app.database import get_db
from app.models import Order as DBOrder

app = FastAPI()
logger = logging.getLogger(__name__)

class CreateOrderModel(BaseModel):
    type_: OrderType = Field(..., alias="type")
    side: OrderSide
    instrument: constr(min_length=12, max_length=12)
    limit_price: Optional[condecimal(decimal_places=2)]
    quantity: conint(gt=0)

    @root_validator
    def validate_order(cls, values):
        if values.get("type_") == "market" and values.get("limit_price"):
            raise ValueError("Market orders cannot have limit_price")
        if values.get("type_") == "limit" and not values.get("limit_price"):
            raise ValueError("Limit orders require limit_price")
        return values

class CreateOrderResponseModel(PydanticOrder):
    pass

async def process_order_placement(order: PydanticOrder, db: Session = Depends(get_db)):
    db_order = db.query(DBOrder).filter(DBOrder.id == order.id_).first()
    if not db_order:
        logger.error(f"Order {order.id_} not found in database")
        return

    try:
        place_order(order)
        
        db_order.status = "completed"
        logger.info(f"Order {order.id_} completed", 
                   extra={"instrument": order.instrument})
        
    except OrderPlacementError as e:
        db_order.status = "failed"
        db_order.error_message = str(e)
        logger.warning(f"Order {order.id_} failed: {str(e)}", 
                      extra={"instrument": order.instrument})
        
    except Exception as e:
        db_order.status = "error"
        db_order.error_message = "Internal processing error"
        logger.critical(f"Order {order.id_} errored: {str(e)}", 
                       exc_info=True)
    finally:
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Failed to commit order {order.id_} status: {str(e)}")

@app.post(
    "/orders",
    status_code=201,
    response_model=CreateOrderResponseModel,
    response_model_by_alias=True
)
async def create_order(
    order_data: CreateOrderModel,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        db_order = DBOrder(
            type=order_data.type_,
            side=order_data.side,
            instrument=order_data.instrument,
            limit_price=order_data.limit_price,
            quantity=order_data.quantity,
            status="pending"
        )
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        order_response = CreateOrderResponseModel(
            id=str(db_order.id),
            created_at=db_order.created_at,
            type=db_order.type,
            side=db_order.side,
            instrument=db_order.instrument,
            limit_price=float(db_order.limit_price) if db_order.limit_price else None,
            quantity=db_order.quantity
        )
        background_tasks.add_task(process_order_placement, order_response, db)
        
        return order_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Order creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )