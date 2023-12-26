from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Owner(Base):
    __tablename__ = "owner"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)


class Company(Base):
    __tablename__ = "company"

    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    owner = Column(String)
    image = Column(String)


class Product(Base):
    __tablename__ = "product"

    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    company = Column(String)
    price = Column(Integer, )
    image = Column(String)

class ProductUpdate(BaseModel):
    title: str
    description: str
    company: str
    price: int
    image: str

class CompanyUpdate(BaseModel):
    title: str
    description: str
    owner: str
    image: str

class OwnerUpdate(BaseModel):
    name: str
