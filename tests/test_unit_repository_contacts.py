import unittest
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.model import Contact, User
from src.schemas.contact import ContactSchema, ContactUpdateSchema
from src.repository.contacts import get_contacts, get_contact, create_contact, update_contact, delete_contact, search_contact, upcoming_birthdays


class TestAsyncContacts(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.user = User(id=1, username='test_user', password="qwerty", confirmed=True)
        self.session = AsyncMock(spec=AsyncSession)

    async def test_get_contacts(self):
        limit = 10
        offset = 0
        contacts = [
            Contact(id=1, first_name='John', last_name='Doe', email='john.doe@example.com', user=self.user),
            Contact(id=2, first_name='Jane', last_name='Smith', email='jane.smith@example.com', user=self.user),
        ]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts

        result = await get_contacts(limit, offset, self.session, self.user)
        self.assertEqual(result, contacts)

    async def test_get_contact(self):
        contact_id = 1
        contact = Contact(id=contact_id, first_name='John', last_name='Doe', email='john.doe@example.com', user=self.user)
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = contact
        self.session.execute.return_value = mocked_contact

        result = await get_contact(contact_id, self.session, self.user)
        self.assertEqual(result, contact)

    async def test_create_contact(self):
        body = ContactSchema(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone='1234567890',
            born_date='1990-01-01'
        )
        result = await create_contact(body, self.session, self.user)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.email, body.email)
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()

    async def test_update_contact(self):
        contact_id = 1
        body = ContactUpdateSchema(
            first_name='John Updated',
            last_name='Doe Updated',
            email='john.updated@example.com',
            phone='0987654321',
            born_date='1989-12-31'
        )
        contact = Contact(id=contact_id, first_name='John', last_name='Doe', email='john.doe@example.com', user=self.user)
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = contact
        self.session.execute.return_value = mocked_contact

        result = await update_contact(contact_id, body, self.session, self.user)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.email, body.email)
        self.session.commit.assert_called_once()

    async def test_delete_contact(self):
        contact_id = 1
        contact = Contact(id=contact_id, first_name='John', last_name='Doe', email='john.doe@example.com', user=self.user)
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = contact
        self.session.execute.return_value = mocked_contact

        result = await delete_contact(contact_id, self.session, self.user)
        self.session.delete.assert_called_once_with(contact)
        self.session.commit.assert_called_once()
        self.assertEqual(result, contact)

    async def test_search_contact(self):
        query = 'John'
        contacts = [
            Contact(id=1, first_name='John', last_name='Doe', email='john.doe@example.com', user=self.user)
        ]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts

        result = await search_contact(query, self.session, self.user)
        self.assertEqual(result, contacts)

    async def test_upcoming_birthdays(self):
        contacts = [
            Contact(id=1, first_name='John', last_name='Doe', email='john.doe@example.com', born_date='1990-01-01', user=self.user),
            Contact(id=2, first_name='Jane', last_name='Smith', email='jane.smith@example.com', born_date='1995-01-02', user=self.user),
        ]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts

        result = await upcoming_birthdays(self.session, self.user)
        self.assertEqual(result, contacts)
