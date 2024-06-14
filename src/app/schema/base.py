import datetime
import uuid
from typing import Any, List, Optional, Dict
from fastapi import Query
from pydantic import BaseModel,Field


class PageSchema(BaseModel):
    page : int = Query(1)
    limit: int = Query(50)
    sort : str = Query(...)
