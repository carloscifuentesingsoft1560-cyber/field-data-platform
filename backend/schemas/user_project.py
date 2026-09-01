from pydantic import BaseModel


class UserProjectCreate(BaseModel):
    user_id: int
    project_id: int

class UserProjectResponse(BaseModel):
    id: int
    user_id: int
    project_id: int