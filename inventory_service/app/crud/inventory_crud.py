from fastapi import HTTPException, Request
from sqlmodel import Session, select
from app.models.inventory_model import InventoryItem





# Add a new product in database

def add_new_inventory_item(inventory_item_data: InventoryItem, session: Session):
    print("Adding Inventory item in database")
    session.add(inventory_item_data)
    session.commit()
    session.refresh(inventory_item_data)
    return inventory_item_data

# Get all products

def get_all_inventory_items(session: Session):
    all_inventory_items = session.exec(select(InventoryItem)).all()
    return all_inventory_items

# Get product by id

def get_inventory_by_id(inventory_item_id: int, session: Session):
    product = session.exec(select(InventoryItem).where(InventoryItem.id == inventory_item_id)).one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Inventory Item is not found")
    return product

# Delete product by id

def delete_inventory_by_id(inventory_item_id: int, session: Session):
    product = session.exec(select(InventoryItem).where(inventory_item_id.id == inventory_item_id)).one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="nventory Item  is not found")
    session.delete(product)
    session.commit()
    return {"message": "Inventory deleted successfully"}

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
