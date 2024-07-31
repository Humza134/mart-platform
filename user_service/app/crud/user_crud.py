import json
from aiokafka import AIOKafkaProducer
from sqlmodel import Session, select
from typing import Annotated, Union
from fastapi import Depends, HTTPException
from app.models.user_model import RegisterUser, User, Role
from app.utils import get_password_hash
from app.deps import get_kafka_producer

class InvalidUserException(Exception):
    def __init__(self, status_code:int, detail:str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def get_user(db:Session, username: Union[str, None] = None):
    try:
        if username is None:
            raise InvalidUserException(status_code=400, detail="Username is required")
        user = db.exec(select(User).where(User.username == username)).one()
        if not user:
            raise InvalidUserException(status_code=404, detail="User not found")
        print("user", user)
        return user
    except InvalidUserException:
        raise
    except Exception as e:
        raise InvalidUserException(status_code=500, detail=str(e))
    


async def db_signup_user(user_data: RegisterUser, db:Session, producer: AIOKafkaProducer):
    # print("Data from client:", user_data)
    # Check user is already registered

    existing_user_email = db.exec(select(User).where(User.username == user_data.username)).first()
    if existing_user_email:
        raise HTTPException(status_code=400, detail="User already registered")

    existing_user = db.exec(select(User).where(User.username == user_data.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already registered")
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)

    # Create new user instance
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        fullname=user_data.fullname,
        hashed_password=hashed_password,
        role=user_data.role
    )

    
    # Add new user to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # produce kafka message excluding password

    # Create dictionary with user data (excluding password)
    user_dict = {field: getattr(new_user, field) for field in new_user.dict() if field != "hashed_password"}

    # Convert the dictionary to a JSON string and encode as UTF-8
    user_json = json.dumps(user_dict).encode("utf-8")

    #  user_data_dict = {
    #     'user_id': new_user.id,
    #     'username': new_user.username,
    #     'email': new_user.email,
    #     'fullname': new_user.fullname,
    #     'role': new_user.role
    # }

    # # Convert the dictionary to a JSON string and encode as UTF-8
    # user_json = json.dumps(user_data_dict).encode('utf-8')

    # Print the JSON (for debugging purposes)
    print("User JSON: ", user_json)

    # Produce Kafka message
    await producer.send_and_wait(
        topic="user-add",
        key=str(new_user.id).encode('utf-8'),
        value=user_json
    )
    
    
    return new_user
