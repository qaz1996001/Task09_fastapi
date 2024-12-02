import datetime
import uuid
from typing import Any, List, Optional, Dict,Union
from pydantic import BaseModel


class ProjectStudyOutput(BaseModel):
    data: Dict[str, Any]
    class Config:
        extra = "ignore"


class ProjectStudyPost(BaseModel):
    project_uid    : Union[uuid.UUID,str]
    study_uid_list : List[Union[uuid.UUID,str]]
    class Config:
        extra = "ignore"