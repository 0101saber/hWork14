from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.model import Contact, User
from src.schemas.contact import ContactSchema, ContactUpdateSchema


async def get_contacts(limit: int, offset: int, db: AsyncSession, user: User):
    """
    Retrieves a list of contacts for a specific user with specified pagination parameters.

    :param offset: int: The number of notes to skip.
    :param limit: int: The maximum number of notes to return.
    :param user: User: The user to retrieve notes for.
    :param db: db: The database session.
    :return: List[Note]: A list of notes.
    """
    stmt = select(Contact).filter_by(user=user).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_contact(contact_id: int, db: AsyncSession, user: User):
    """
    Retrieves a specific contact by its ID for a specific user.

    :param contact_id: int: The unique identifier of the contact.
    :param db: AsyncSession: The database session.
    :param user: User: The user associated with the contact.
    :return: Contact | None: The contact object if found, otherwise None.
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(stmt)
    return contact.scalar_one_or_none()


async def create_contact(body: ContactSchema, db: AsyncSession, user: User):
    """
    Creates a new contact for a specific user.

    :param data: dict: The data for creating the new contact (e.g., name, email, phone, etc.).
    :param db: AsyncSession: The database session.
    :param user: User: The user for whom the contact is being created.
    :return: Contact: The created contact object.
    """
    contact = Contact(**body.model_dump(exclude_unset=True), user=user)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactUpdateSchema, db: AsyncSession, user: User):
    """
    Updates an existing contact for a specific user.

    :param contact_id: int: The unique identifier of the contact to update.
    :param data: dict: The updated data for the contact (e.g., name, email, phone, etc.).
    :param db: AsyncSession: The database session.
    :param user: User: The user associated with the contact.
    :return: Contact | None: The updated contact object if found, otherwise None.
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact:
        contact.first_name = body.first_name
        contact.last_name = body.last_name
        contact.email = body.email
        contact.phone = body.phone
        contact.born_date = body.born_date
        contact.delete = body.delete
        await db.commit()
        await db.refresh(contact)
    return contact


async def delete_contact(contact_id: int, db: AsyncSession, user: User):
    """
    Deletes a specific contact for a specific user.

    :param contact_id: int: The unique identifier of the contact to delete.
    :param db: AsyncSession: The database session.
    :param user: User: The user associated with the contact.
    :return: bool: True if the contact was successfully deleted, otherwise False.
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    contact = await db.execute(stmt)
    contact = contact.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact


async def search_contact(query: str, db: AsyncSession, user: User):
    """
     Searches for contacts that match a specific query for a specific user.

     :param query: str: The search query to match against contact names, emails, or other fields.
     :param db: AsyncSession: The database session.
     :param user: User: The user associated with the contacts.
     :return: List[Contact]: A list of contacts that match the search query.
     """
    stmt = select(Contact).filter(
        (Contact.first_name.ilike(f"%{query}%"))
        | (Contact.last_name.ilike(f"%{query}%"))
        | (Contact.email.ilike(f"%{query}%")),
        Contact.user == user
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def upcoming_birthdays(db: AsyncSession, user: User):
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    stmt = select(Contact).filter(Contact.born_date.between(today, next_week)).filter_by(user=user)
    result = await db.execute(stmt)
    return result.scalars().all()
