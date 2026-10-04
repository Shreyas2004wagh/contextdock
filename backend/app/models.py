from pydantic import BaseModel, ConfigDict, Field


class InputModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class ProjectCreate(InputModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=500)


class RememberTextRequest(InputModel):
    project_id: str = Field(min_length=1, max_length=80)
    content: str = Field(min_length=1, max_length=200_000)
    title: str = Field(default="Memory note", max_length=120)


class RememberUrlRequest(InputModel):
    project_id: str = Field(min_length=1, max_length=80)
    url: str = Field(min_length=1, max_length=2048)


class RememberSessionRequest(InputModel):
    project_id: str = Field(min_length=1, max_length=80)
    summary: str = Field(min_length=1, max_length=40_000)
    files_changed: str = Field(default="", max_length=40_000)
    commands_run: str = Field(default="", max_length=40_000)
    decisions: str = Field(default="", max_length=40_000)
    blockers: str = Field(default="", max_length=40_000)
    next_tasks: str = Field(default="", max_length=40_000)


class RecallRequest(InputModel):
    project_id: str = Field(min_length=1, max_length=80)
    query: str = Field(min_length=1, max_length=8000)


class ImproveRequest(InputModel):
    project_id: str = Field(min_length=1, max_length=80)


class ForgetRequest(InputModel):
    project_id: str = Field(min_length=1, max_length=80)
