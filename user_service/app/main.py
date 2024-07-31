from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, Depends, Form, HTTPException, status
from typing import Annotated, Union
from contextlib import asynccontextmanager
from jose import JWTError, jwt
from fastapi.security import  OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlmodel import Session
from app.models.user_model import RegisterUser, TokenData, User, Role
from app.deps import get_kafka_producer, get_session
from app.settings import SECRET_KEY,ALGORITHM,ACCESS_TOKEN_EXPIRE_MINUTES,REFRESH_TOKEN_EXPIRE_MINUTES
from app.models.user_model import UserRead,RegisterUser,LoginResponse, User
from app.db_engine import engine
from sqlmodel import Field, Session, SQLModel
from app.crud.user_crud import db_signup_user, get_user, InvalidUserException
from datetime import datetime, timedelta, timezone
from app.utils import verify_password, create_refresh_token



def create_db_and_tables()->None:
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan, title="Auth server")


oauth_scheme = OAuth2PasswordBearer(tokenUrl="/api/oauth/login")


def authenticate_user(db, username: str, password:str):
    try:
        user = get_user(db, username)
        if not user:
            return False
    
        if not verify_password(password, user.hashed_password):
            return False
        return user

    except InvalidUserException:
        raise


# create a access token

def create_access_token(data:dict, expires_delta:Union[timedelta, None] = None):
    to_encode = data.copy()

    # if not isinstance(SECRET_KEY, str):
    #     raise ValueError("SECRET_KEY must be a string")
    # if not isinstance(ALGORITHM, str):
    #     raise ValueError("ALGORITHM must be a string")
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, str(SECRET_KEY), algorithm = str(ALGORITHM))

    return encoded_jwt

async def get_currnet_user(token:  Annotated[str, Depends(oauth_scheme)],db: Annotated[Session, Depends(get_session)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail= "Could not validate creddentials",
        headers= {"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, str(SECRET_KEY), algorithms=str(ALGORITHM))
        username: str | None = payload.get("sub")

        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(db, username = token_data.username)
    if user is None:
        raise credentials_exception
    return user



# login user

@app.post("/api/oauth/login", response_model=LoginResponse, tags=["OAuth2 Authentication"])
async def service_login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm,Depends()],db:Annotated[Session , Depends(get_session)]):
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=float(str(ACCESS_TOKEN_EXPIRE_MINUTES)))
        access_token = create_access_token(
            data={"sub": user.username, "id": user.id},expires_delta=access_token_expires
        )

        # Generate refresh token (you might want to set a longer expiry for this)
        refresh_token_expires = timedelta(
            minutes=float(str(REFRESH_TOKEN_EXPIRE_MINUTES)))
        refresh_token = create_refresh_token(
            data={"sub": user.username, "id": user.id}, expires_delta=refresh_token_expires)

        return {"access_token": access_token, "token_type": "bearer", "user": user,"expires_in": int(access_token_expires.total_seconds()), "refresh_token": refresh_token}
    
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect access or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
# signup user 
@app.post("/api/oauth/signup", response_model=UserRead, tags=["OAuth2 Authentication"])
async def signup_user(user_data: RegisterUser, db: Annotated[Session, Depends(get_session)], producer: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)]):

    return await db_signup_user(user_data, db, producer)

@app.get("/admin/", response_model=UserRead)
async def check_is_admin(current_user: User = Depends(get_currnet_user)):
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=400,
            detail="Not enough permissions",
        )
    return current_user
    
@app.get("/user/me", response_model=UserRead)
async def get_current_active_user(current_user: User = Depends(get_currnet_user)):
    if current_user.role not in (Role.USER, Role.ADMIN):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user