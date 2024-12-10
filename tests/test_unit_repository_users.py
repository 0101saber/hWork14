import unittest
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.model import User
from src.schemas.user import UserSchema
from src.repository.users import get_user_by_email, create_user, update_token, confirmed_email


class TestAsyncUsers(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.user = User(
            id=1,
            username="test_user",
            email="test@example.com",
            password="hashed_password",
            confirmed=False
        )
        self.session = AsyncMock(spec=AsyncSession)

    async def test_get_user_by_email(self):
        email = "test@example.com"
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mocked_user

        result = await get_user_by_email(email, self.session)
        self.assertEqual(result, self.user)

    async def test_create_user(self):
        body = UserSchema(
            username="new_user",
            email="new_user@example.com",
            password="new_password"
        )

        result = await create_user(body, self.session)
        self.assertIsInstance(result, User)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.username, body.username)
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()

    async def test_update_token(self):
        token = "new_refresh_token"
        await update_token(self.user, token, self.session)

        self.assertEqual(self.user.refresh_token, token)
        self.session.commit.assert_called_once()

    async def test_confirmed_email(self):
        email = "test@example.com"
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mocked_user

        await confirmed_email(email, self.session)

        self.assertTrue(self.user.confirmed)
        self.session.commit.assert_called_once()
