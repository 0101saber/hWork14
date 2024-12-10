from typing import Optional

from pydantic import BaseModel, EmailStr, Field, PastDate


class ContactSchema(BaseModel):
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=100)
    email: str = EmailStr()
    phone: str = Field(None, example="012 234 56 78")
    born_date: str = PastDate()


class ContactUpdateSchema(ContactSchema):
    delete: bool


class ContactResponse(ContactSchema):
    id: int = 1
    first_name: str
    last_name: str
    email: str
    phone: str
    born_date: str

    class Config:
        from_attributes = True
