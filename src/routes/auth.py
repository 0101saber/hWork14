from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from src.database.db import get_db
from src.repository import users as users_repository
from src.schemas.user import UserSchema, TokenSchema, UserResponse, RequestEmail
from src.services.auth import auth_service
from src.services.email import send_email

router = APIRouter(prefix="/auth", tags=["auth"])
refresh_token = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserSchema, bt: BackgroundTasks, request: Request, db: AsyncSession = Depends(get_db)):
    """
     Registers a new user account.

     :param body: UserSchema: The registration details (email, password, etc.).
     :param bt: BackgroundTasks: The background task manager for sending confirmation emails.
     :param request: Request: The HTTP request object to generate the confirmation email link.
     :param db: AsyncSession: The database session (provided by dependency injection).
     :return: UserResponse: The created user's data.
     :raises HTTPException: 409 if the user already exists.
     """
    exist_user = await users_repository.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await users_repository.create_user(body, db)
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user


@router.post("/login", response_model=TokenSchema)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Authenticates a user and generates JWT access and refresh tokens.

    :param body: OAuth2PasswordRequestForm: The user's login credentials (email and password).
    :param db: AsyncSession: The database session (provided by dependency injection).
    :return: TokenSchema: The access and refresh tokens.
    :raises HTTPException: 401 if the email is invalid, email is unconfirmed, or the password is incorrect.
    """
    user = await users_repository.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await users_repository.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/refresh_token', response_model=TokenSchema)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(refresh_token),
                        db: AsyncSession = Depends(get_db)):
    """
    Refreshes the user's access and refresh tokens.

    :param credentials: HTTPAuthorizationCredentials: The refresh token from the Authorization header.
    :param db: AsyncSession: The database session (provided by dependency injection).
    :return: TokenSchema: The new access and refresh tokens.
    :raises HTTPException: 401 if the refresh token is invalid or does not match the user's stored token.
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await users_repository.get_user_by_email(email, db)
    if user.refresh_token != token:
        await users_repository.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await users_repository.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
     Confirms a user's email address using a verification token.

     :param token: str: The email verification token.
     :param db: AsyncSession: The database session (provided by dependency injection).
     :return: dict: A message indicating the email confirmation status.
     :raises HTTPException: 400 if the token is invalid or the user does not exist.
     """
    email = await auth_service.get_email_from_token(token)
    user = await users_repository.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await users_repository.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: AsyncSession = Depends(get_db)):
    """
    Sends an email verification request to a user.

    :param body: RequestEmail: The user's email address for verification.
    :param background_tasks: BackgroundTasks: The background task manager for sending the email.
    :param request: Request: The HTTP request object to generate the confirmation email link.
    :param db: AsyncSession: The database session (provided by dependency injection).
    :return: dict: A message confirming that the email has been sent.
    """
    user = await users_repository.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
    return {"message": "Check your email for confirmation."}
