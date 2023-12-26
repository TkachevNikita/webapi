import asyncio
import json
import uuid

from fastapi_users import FastAPIUsers
from fastapi import FastAPI, Depends, HTTPException
from starlette.websockets import WebSocket, WebSocketDisconnect

from CRUD import get_data, delete_data
from auth.auth import auth_backend
from auth.manager import get_user_manager
from auth.schemas import UserRead, UserCreate
from database import User, create_db_and_tables, async_session_maker
from models import Product, ProductUpdate, Owner, Company, OwnerUpdate, CompanyUpdate

app = FastAPI()

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["AUTH"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["AUTH"],
)

current_user = fastapi_users.current_user()


@app.post("/add_to_bucket", tags=["USERS"])
async def add_to_bucket(product_id: str, user: User = Depends(current_user)):
    async with async_session_maker() as session:
        loaded_user = await session.merge(user)
        products_list = json.loads(loaded_user.products)
        if product_id not in products_list:
            products_list[product_id] = 1
        else:
            products_list[product_id] += 1
        loaded_user.products = json.dumps(products_list)
        await session.commit()
        await session.refresh(loaded_user)
    return loaded_user

@app.delete("/remove_product", tags=["USERS"])
async def add_to_bucket(product_id: str, user: User = Depends(current_user)):
    async with async_session_maker() as session:
        loaded_user = await session.merge(user)
        products_list = json.loads(loaded_user.products)
        if product_id not in products_list:
            raise HTTPException(status_code=404, detail="Item not found")
        if products_list[product_id] <= 1:
            del products_list[product_id]
        else:
            products_list[product_id] -= 1
        loaded_user.products = json.dumps(products_list)
        await session.commit()
        await session.refresh(loaded_user)
    return loaded_user

@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()


@app.post("/products", tags=["PRODUCTS"])
async def add_product(product: ProductUpdate):
    async with async_session_maker() as session:
        async with session.begin():
            new_product = Product(
                image=product.image,
                title=product.title,
                id=str(uuid.uuid4()),
                price=product.price,
                company=product.company,
                description=product.description
            )
            session.add(new_product)
        await session.commit()
        await session.refresh(new_product)
    return new_product


@app.get("/products", tags=["PRODUCTS"])
async def get_products():
    return await get_data(Product)


@app.delete("/products/{product_id}", tags=["PRODUCTS"])
async def delete_product(product_id: str):
    return await delete_data(Product, product_id)


@app.put("/products/{id}", tags=["PRODUCTS"])
async def update_product(id: str, product_update: ProductUpdate):
    async with async_session_maker() as session:
        async with session.begin():
            product = await session.get(Product, id)
            if product is None:
                raise HTTPException()
            product.title = product_update.title
            product.description = product_update.description
            product.company = product_update.company
            product.price = product_update.price
            product.image = product_update.image

            await session.commit()


@app.get("/companies", tags=["COMPANIES"])
async def get_companies():
    return await get_data(Company)


@app.post("/companies", tags=["COMPANIES"])
async def add_company(company: CompanyUpdate):
    async with async_session_maker() as session:
        async with session.begin():
            new_company = Company(
                id=str(uuid.uuid4()),
                image=company.image,
                owner=company.owner,
                description=company.description,
                title=company.title
            )
            session.add(new_company)
        await session.commit()
        await session.refresh(new_company)
    return new_company


@app.delete("/companies/{id}", tags=["COMPANIES"])
async def delete_company(id: str):
    return await delete_data(Company, id)


@app.put("/companies/{id}", tags=["COMPANIES"])
async def update_company(id: str, company_update: CompanyUpdate):
    async with async_session_maker() as session:
        async with session.begin():
            company = await session.get(Company, id)
            if company is None:
                raise HTTPException()
            company.title = company_update.title
            company.description = company_update.description
            company.image = company_update.image
            company.owner = company_update.owner

            await session.commit()


@app.post("/owners", tags=["OWNERS"])
async def post_owner(owner: OwnerUpdate):
    async with async_session_maker() as session:
        async with session.begin():
            new_owner = Owner(
                name=owner.name,
                id=str(uuid.uuid4()),
            )
            session.add(new_owner)
        await session.commit()
        await session.refresh(new_owner)
    return new_owner


@app.get("/owners", tags=["OWNERS"])
async def get_owners():
    return await get_data(Owner)


@app.delete("/owners/{id}", tags=["OWNERS"])
async def get_owners(id: str):
    return await delete_data(Owner, id)


@app.put("/owners/{id}", tags=["OWNERS"])
async def update_owner(id: str, owner_update: OwnerUpdate):
    async with async_session_maker() as session:
        async with session.begin():
            owner = await session.get(Owner, id)
            if owner is None:
                raise HTTPException()
            owner.name = owner_update.name

            await session.commit()

connected_websockets = set()


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(30)
            async with async_session_maker() as session:
                async with session.begin():
                    user = await session.get(User, user_id)
                    await session.commit()
            n = json.loads(user.products)
            if len(n) > 0:
                await websocket.send_text(f"В вашей корзине есть {sum(n.values())} товаров. Откройте корзину для дальнейшего оформления.")
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)
