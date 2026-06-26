from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=500)


class RememberTextRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=80)
    content: str = Field(min_length=1)
    title: str = Field(default="Memory note", max_length=120)


class RememberUrlRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=80)
    url: str = Field(min_length=1)


class RecallRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=80)
    query: str = Field(min_length=1)


class ImproveRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=80)


class ForgetRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=80)

