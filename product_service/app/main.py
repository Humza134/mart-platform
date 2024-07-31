# main.py
from contextlib import asynccontextmanager
import time
from typing import Union, Optional, Annotated
from app.db_engine import engine
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi import FastAPI, Depends, HTTPException
from typing import AsyncGenerator
from aiokafka import AIOKafkaProducer
import asyncio
import json
from app import todo_pb2
from app.deps import get_kafka_producer, get_session
from app.crud.product_crud import add_new_product, get_all_products, get_product_by_id, delete_product_by_id, update_product_by_id
from app.models.product_model import Product, ProductUpdate, ProductCreate
from app import settings
from app.consumers.product_consumer import consume_messages
from app.consumers.inventory_consumer import inventory_consume_messages
# import httpx
# from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# call user service and get user
# def get_current_user_dep(token: Annotated[str | None, Depends(oauth2_scheme)]):
#      print("Token: ", token)
#      url = f"http://user_service:8007/user/me"
#      headers = {"Authorization": f"Bearer {token}"}

#      response = httpx.get(url, headers=headers)
#      # print("User :", response.json())
#      if response.status_code == 200:
#           return response.json()
#      else:
#         raise HTTPException(status_code=response.status_code, detail=response.json().get('detail'))


# # call user service and get user admin
# def get_admin_dep(token: Annotated[str | None, Depends(oauth2_scheme)]):
#      print("Token: ", token)
#      url = f"http://user_service:8007/admin/"
#      headers = {"Authorization": f"Bearer {token}"}

#      response = httpx.get(url, headers=headers)
#      # print("User :", response.json())
#      if response.status_code == 200:
#           return response.json()
#      else:
#         raise HTTPException(status_code=response.status_code, detail=response.json().get('detail'))

# def login_with_retry(url, data):
#     max_retries = 5
#     for attempt in range(max_retries):
#         try:
#             response = httpx.post(url, data=data)
#             response.raise_for_status()  # Raises an exception for 4x/5x responses
#             return response
#         except (httpx.ConnectError, httpx.HTTPStatusError) as exc:
#             if attempt < max_retries - 1:
#                 time.sleep(2 ** attempt)
#                 logger.warning(f"Retry {attempt + 1} for {url} due to {exc}")
#             else:
#                 logger.error(f"Failed to connect to {url} after {max_retries} attempts")
#                 raise exc

# @app.post("/auth/login")
# def login_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
#     url = f"http://user_service:8007/api/oauth/login"
#     data = {
#         "username": form_data.username,
#         "password": form_data.password
#     }
#     logger.info(f"Connecting to URL: {url}")
#     try:
#         response = login_with_retry(url, data)
#         logger.info(f"Received Response: {response.json()}")
#         if response.status_code == 200:
#             return response.json()
#         logger.error(f"Login failed with status code: {response.status_code}")
#         raise HTTPException(status_code=response.status_code, detail=response.json().get('detail'))
#     except httpx.HTTPError as e:
#         logger.error(f"HTTP error occurred: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def read_root():
    return {"Hello": "PanaCloud"}


@app.post("/manage-product/", response_model=Product)
async def create_product(product: ProductCreate, session: Annotated[Session, Depends(get_session)], producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]):
     
     # owner_id = owner["id"]
     # print("data from client: ", product)
     validate_product = Product.model_validate(product)
     # validate_product.owner_id = owner_id
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