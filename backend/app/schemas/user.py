from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    email: str
    phone: str | None = None
    role: str = "user"
    password: str | None = "user123"


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None
    role: str

    model_config = {
        "from_attributes": True
    }