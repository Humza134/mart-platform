from fastapi import HTTPException, Request
from sqlmodel import Session, select
from app.models.product_model import Product, ProductUpdate


# Add a new product in database

def add_new_product(product_data: Product, session: Session):
    print("Adding products in database")
    session.add(product_data)
    session.commit()
    session.refresh(product_data)
    return product_data

# Get all products

def get_all_products(session: Session):
    all_products = session.exec(select(Product)).all()
    return all_products

# Get product by id

def get_product_by_id(product_id: int, session: Session):
    product = session.exec(select(Product).where(Product.id == product_id)).one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product is not found")
    return product

# Delete product by id

def delete_product_by_id(product_id: int, session: Session):
    product = session.exec(select(Product).where(Product.id == product_id)).one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product is not found")
    session.delete(product)
    session.commit()
    return {"message": "Product deleted successfully"}

# update product

def update_product_by_id(product_id: int, to_update_product_data: ProductUpdate, session: Session):
    product = session.exec(select(Product).where(Product.id == product_id)).one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product is not found")
    # update the product
    update_product = to_update_product_data.model_dump(exclude_unset=True)
    product.sqlmodel_update(update_product)
    session.add(product)
    session.commit()
    return product

# validate product by id

def validate_product_by_id(product_id: int, session: Session)-> Product | None:
    product = session.exec(select(Product).where(Product.id == product_id)).one_or_none()
    return product
