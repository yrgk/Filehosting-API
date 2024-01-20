from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    id: int
    name: str
    email: EmailStr

class UserAdd(BaseModel):
    name: str
    email: EmailStr
    password: str


class RepositoryItem(BaseModel):
    id: int
    view_name: str
    name: str
    link: str
    user_api_key: str


class FileItem(BaseModel):
    id: int
    view_name: str
    name: str
    download_link: str
    rep_id: int


class OneRepository(BaseModel):
    name: str
    files: list[FileItem]