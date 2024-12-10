from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.model import User
from src.schemas.user import UserSchema, UserResponse
from libgravatar import Gravatar


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieves a user by their email address.

    :param email: str: The email address of the user to retrieve.
    :param db: AsyncSession: The database session (provided by dependency injection).
    :return: User | None: The user object if found, otherwise None.
    """
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def create_user(body: UserSchema, db: AsyncSession = Depends(get_db)):
    """
     Creates a new user in the database.

     :param body: UserSchema: The user data to create the new user (e.g., email, password, etc.).
     :param db: AsyncSession: The database session (provided by dependency injection).
     :return: User: The created user object.
     """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)

    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession):
    """
       Updates the refresh token for a specific user.

       :param user: User: The user object whose token needs to be updated.
       :param token: str | None: The new refresh token to associate with the user (or None to clear it).
       :param db: AsyncSession: The database session.
       :return: None
       """
    user.refresh_token = token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession) -> None:
    """
    Confirms the email address for a specific user.

    :param email: str: The email address of the user to confirm.
    :param db: AsyncSession: The database session.
    :return: None
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()
