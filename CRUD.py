from fastapi import HTTPException
from sqlalchemy import select

from database import async_session_maker


async def get_data(model):
    async with async_session_maker() as session:
        result = await session.execute(select(model))
        data = result.scalars().all()
    return data


async def delete_data(model, id):
    async with async_session_maker() as session:
        async with session.begin():
            item = await session.get(model, id)
            if item is None:
                raise HTTPException(status_code=404, detail="Item not found")

            await session.delete(item)
            await session.commit()

    return {"message": "Item deleted successfully"}