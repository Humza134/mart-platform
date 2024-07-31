from fastapi import HTTPException, Request
from sqlmodel import Session, select
from app.models.order_model import Order





# Add a new order in database


def add_order(order_data: Order, session: Session):
    print("Adding order in database")
    session.add(order_data)
    session.commit()
    session.refresh(order_data)
    return order_data

# Get all orders

def get_all_orders(session: Session):
    all_orders = session.exec(select(Order)).all()
    return all_orders

# Get product by id

def get_order_by_id(order_id: int, session: Session):
    order = session.exec(select(Order).where(Order.id == order_id)).one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order is not found")
    return order

# Delete order by id

def delete_order_by_id(order_id: int, session: Session):
    order = session.exec(select(Order).where(Order.id == order_id)).one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order is not found")
    session.delete(order)
    session.commit()
    return {"message": "order deleted successfully"}

# update product

# def update_inventory_by_id(inventory_item_id: int, to_update_product_data: ProductUpdate, session: Session):
#     product = session.exec(select(InventoryItem).where(InventoryItem.id == inventory_item_id)).one_or_none()
#     if product is None:
#         raise HTTPException(status_code=404, detail="nventory Item  is not found")
#     # update the product
#     update_product = to_update_product_data.model_dump(exclude_unset=True)
#     product.sqlmodel_update(update_product)
#     session.add(product)
#     session.commit()
#     return product
