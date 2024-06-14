from typing import Annotated

from sqlalchemy.orm import Session
from fastapi import Depends


from app.core import security
from app.core.config import settings
from app.core.db import engine,SessionLocal


# def get_db() -> Generator[Session, None, None]:
#     with Session(engine) as session:
#         yield session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SessionDep = Annotated[Session, Depends(get_db)]
