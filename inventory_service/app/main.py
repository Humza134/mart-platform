# main.py
from contextlib import asynccontextmanager
from typing import Union, Optional, Annotated
from app.db_engine import engine
from sqlmodel import Field, Session, SQLModel, create_engine, select, Sequence
from fastapi import FastAPI, Depends, HTTPException
from typing import AsyncGenerator
from aiokafka import AIOKafkaProducer
import asyncio
import json
from app import todo_pb2
from app.deps import get_kafka_producer, get_session
from app.crud.inventory_crud import get_all_inventory_items, get_inventory_by_id, delete_inventory_by_id
from app.models.inventory_model import InventoryItem
from app.consumers.stock_consumer import consume_messages




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
    task = asyncio.create_task(consume_messages("inventory-add-stock-response", 'broker:19092'))
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


@app.post("/manage-inventory/", response_model=InventoryItem)
async def create_new_inventory_item(item: InventoryItem, session: Annotated[Session, Depends(get_session)], producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]):

     # print("data from client: ", product)
     # validate_product = Product.model_validate(product)
     # print("data after validation")

     # Create a new product and send it to kafka

     item_dict = {field: getattr(item, field) for field in item.dict()}
     item_json = json.dumps(item_dict).encode("utf-8")
     print("Product JSON: ", item_json)
     # produce message
     await producer.send_and_wait("AddStock", item_json)
     # return add_new_product(product_data=product_data, session=session)
     return item



#         todo_protobuf = todo_pb2.Todo(id=todo.id, content=todo.content)
#         print(f"Todo protobuf: {todo_protobuf}")
#         # Serialize the message to a byte string
#         serialized_todo = todo_protobuf.SerializeToString()
#         print(f"Serialized data: {serialized_todo}")
#         # Produce message
#         await producer.send_and_wait("todos", serialized_todo)
        


@app.get("/manage-inventory/all", response_model=list[InventoryItem])
def call_all_inventory_items(session: Annotated[Session, Depends(get_session)]):
        # Get all inventory item
        return get_all_inventory_items( session)
        # todos = session.exec(select(Todo)).all()
        # return todos

@app.get("/manage-inventory/{item_id}", response_model=InventoryItem)
def get_single_inventory_item(item_id: int, session: Annotated[Session, Depends(get_session)]):
     # Get single inventory item by id
     try:
          return get_inventory_by_id(inventory_item_id=item_id, session=session)
     except HTTPException as e:
          raise e
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
     
@app.delete("/manage-inventory/{item_id}", response_model=dict)
def delete_inventory_item(item_id: int, session: Annotated[Session, Depends(get_session)]):
     # Delete inventory 
     try:
          return delete_inventory_by_id(inventory_item_id=item_id, session=session)
     except HTTPException as e:
          raise e
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
     
# @app.patch("/manage-inventory/{item_id}", response_model=Product)
# def update_product(item_id: int, product: ProductUpdate, session: Annotated[Session, Depends(get_session)]):
#      # Update Product
#      try:
#           return update_product_by_id(inventory_item_id=item_id, to_update_product_data=product, session=session)
#      except HTTPException as e:
#           raise e
#      except Exception as e:
#           raise HTTPException(status_code=500, detail=str(e))
     
