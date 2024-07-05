# main.py
from contextlib import asynccontextmanager
from typing import Union, Optional, Annotated
from app.db_engine import engine
from sqlmodel import Field, Session, SQLModel, create_engine, select, Sequence
from fastapi import FastAPI, Depends, HTTPException, Request
from typing import AsyncGenerator
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import asyncio
import json
from app import todo_pb2
from app.deps import get_kafka_producer, get_session
from app.crud.product_crud import add_new_product, get_all_products, get_product_by_id, delete_product_by_id, update_product_by_id
from app.models.product_model import Product, ProductUpdate, ProductCreate
from app import settings
from app.consumers.product_consumer import consume_messages
from app.consumers.inventory_consumer import inventory_consume_messages


def create_db_and_tables()->None:
    SQLModel.metadata.create_all(engine)


# The first part of the function, before the yield, will
# be executed before the application starts.
# https://fastapi.tiangolo.com/advanced/events/#lifespan-function
# loop = asyncio.get_event_loop()
@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncGenerator[None, None]:
    
    print("Creating tables..")
    # loop.run_until_complete(consume_messages('todos', 'broker:19092'))
#   task = asyncio.create_task(consume_messages(settings.KAFKA_PRODUCT_TOPIC, 'broker:19092'))
    task = asyncio.create_task(consume_messages(
         settings.KAFKA_PRODUCT_TOPIC, 'broker:19092'))
    asyncio.create_task(inventory_consume_messages(
         "AddStock", 'broker:19092'
    ))
    
    
    create_db_and_tables()
    print("Startup complete")
    yield


app = FastAPI(lifespan=lifespan, title="Hello World API with DB", 
    version="0.0.1",
    # servers=[
    #     {
    #         "url": "http://127.0.0.1:8000", # ADD NGROK URL Here Before Creating GPT Action
    #         "description": "Development Server"
    #     }
    #     ]
        )



@app.get("/")
def read_root():
    return {"Hello": "PanaCloud"}


@app.post("/manage-product/", response_model=Product)
async def create_product(product: ProductCreate, session: Annotated[Session, Depends(get_session)], producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]):

     # print("data from client: ", product)
     validate_product = Product.model_validate(product)
     # print("data after validation")

     # Create a new product and send it to kafka

     product_dict = {field: getattr(validate_product, field) for field in validate_product.dict()}
     product_json = json.dumps(product_dict).encode("utf-8")
     print("Product JSON: ", product_json)
     # produce message
     await producer.send_and_wait(settings.KAFKA_PRODUCT_TOPIC, product_json)
     # return add_new_product(product_data=product_data, session=session)
     return validate_product



#         todo_protobuf = todo_pb2.Todo(id=todo.id, content=todo.content)
#         print(f"Todo protobuf: {todo_protobuf}")
#         # Serialize the message to a byte string
#         serialized_todo = todo_protobuf.SerializeToString()
#         print(f"Serialized data: {serialized_todo}")
#         # Produce message
#         await producer.send_and_wait("todos", serialized_todo)
        


@app.get("/manage-product/all", response_model=list[Product])
def call_all_products(session: Annotated[Session, Depends(get_session)]):
        # Get all products
        return get_all_products( session)
        # todos = session.exec(select(Todo)).all()
        # return todos

@app.get("/manage-product/{product_id}", response_model=Product)
def get_single_product(product_id: int, session: Annotated[Session, Depends(get_session)]):
     # Get single product by id
     try:
          return get_product_by_id(product_id=product_id, session=session)
     except HTTPException as e:
          raise e
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
     
@app.delete("/manage-product/{product_id}", response_model=dict)
def delete_product(product_id: int, session: Annotated[Session, Depends(get_session)]):
     # Delete Product
     try:
          return delete_product_by_id(product_id=product_id, session=session)
     except HTTPException as e:
          raise e
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
     
@app.patch("/manage-product/{product_id}", response_model=Product)
def update_product(product_id: int, product: ProductUpdate, session: Annotated[Session, Depends(get_session)]):
     # Update Product
     try:
          return update_product_by_id(product_id=product_id, to_update_product_data=product, session=session)
     except HTTPException as e:
          raise e
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
     
@app.get("/products/by-category/{category_id}", response_model=list[Product])
def get_product_by_category(category_id: int, session: Annotated[Session, Depends(get_session)]):
     products = session.exec(select(Product).where(Product.category_id == category_id)).all()
     if products is None:
          raise HTTPException(status_code=404, detail="Products is not found")
     return products