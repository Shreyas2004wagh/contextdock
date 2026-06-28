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


class RememberSessionRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=80)
    summary: str = Field(min_length=1)
    files_changed: str = ""
    commands_run: str = ""
    decisions: str = ""
    blockers: str = ""
    next_tasks: str = ""


class RecallRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=80)
    query: str = Field(min_length=1)


class ImproveRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=80)


class ForgetRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=80)
