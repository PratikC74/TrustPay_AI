from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    email: str
    phone: str | None = None
    role: str = "user"


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None
    role: str

    model_config = {
        "from_attributes": True
    }