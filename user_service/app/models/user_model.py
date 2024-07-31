from sqlmodel import SQLModel,Field,Relationship
from datetime import datetime
from enum import Enum


class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"


class Token(SQLModel):
    access_token: str
    token_type: str
   
class GPTToken(Token):
    expires_in: int
    refresh_token: str

class TokenData(SQLModel):
    username: str | None = None
    id: int | None = None

class UserBase(SQLModel):
    email: str = Field(unique=True, nullable=False)
    username: str = Field(index=True, nullable=False)
    fullname: str = Field(nullable=False)

class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str = Field(nullable=False)
    # created_at: datetime | None = Field(default_factory=datetime.now)
    # updated_at: datetime | None = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now})
    role: Role


class RegisterUser(UserBase):
    password: str = Field(nullable=False)
    role: Role

class UserInDB(UserBase):
    id: int
    hashed_password: str

class UserRead(UserBase):
    id: int
    role: Role
    
class LoginResponse(Token):
    user: UserRead
    expires_in: int
    refresh_token: str

