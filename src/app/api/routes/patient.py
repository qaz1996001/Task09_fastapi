import datetime
from typing import Annotated, Union, Any, List

from fastapi import APIRouter, Depends, HTTPException,Body
from fastapi_pagination import Page,paginate
from fastapi_pagination.api import create_page
from sqlalchemy.sql import Select
from pydantic import BaseModel, Field

from app.core import SessionDep
from app.core.paginate import paginate_items
from app.model.patient import PatientModel


router = APIRouter()


class PatientOut(BaseModel):
    patient_uid : str
    patient_id  : str
    gender      : str
    birth_date  : datetime.date


class FilterItemSchema(BaseModel):
    field :str = Body('gender')
    op    :str = Body('eq')
    value :Any = Body('M')
class FilterSchema(BaseModel):
    filter_ :List[FilterItemSchema] = Body(...)


@router.get("/hello")
async def hello_world():
    return "Hello World!"


@router.get("/")
def get_patient(session: SessionDep) -> Page[PatientOut]:
    patient_items_list, total, raw_params, params = paginate_items(session, Select(PatientModel))
    response_list = []
    for patient_items in patient_items_list:
        patient = patient_items[0]
        response_list.append(PatientOut(patient_uid = patient.uid.hex,
                                        patient_id  = patient.patient_id,
                                        gender      = patient.gender,
                                        birth_date  = patient.birth_date,))
    page: Page[PatientOut] = create_page(response_list, total, params)
    return page


@router.post("/")
def post_patient(filter_schema : FilterSchema,
                 session: SessionDep) -> Page[PatientOut]:
    print('filter_schema')
    print(filter_schema.dict())
    patient_items_list, total, raw_params, params = paginate_items(session, Select(PatientModel))
    response_list = []

    for patient_items in patient_items_list:
        patient = patient_items[0]
        response_list.append(PatientOut(patient_uid =patient.uid.hex,
                                        patient_id  =patient.patient_id,
                                        gender      =patient.gender,
                                        birth_date  =patient.birth_date,))
    page: Page[PatientOut] = create_page(response_list, total, params)
    return page