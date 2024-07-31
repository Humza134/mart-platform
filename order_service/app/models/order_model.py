# from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import List



class OrderBase(SQLModel):
    product_id: int
    quantity: int
    price: int
    

class Order (OrderBase, table=True):
    id: int = Field(default=None, primary_key=True)
    # created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")


class OrderCreate(OrderBase):
    pass

class OrderUpdate(SQLModel):
    status: str | None = None
    product_id: int
    quantity: int
    price: int



    