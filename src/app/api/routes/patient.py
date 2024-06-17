import datetime
from typing import Annotated, Union, Any, List, Literal

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from fastapi_pagination import Page, paginate
from fastapi_pagination.api import create_page
from pydantic import TypeAdapter
# from pydantic.fields import FieldInfo
# from pydantic.json_schema import DEFAULT_REF_TEMPLATE, GenerateJsonSchema, JsonSchemaMode
# from pydantic.main import IncEx
# from pydantic_core import PydanticUndefined
from sqlalchemy import func, or_, any_,text
from sqlalchemy.sql import Select
from sqlalchemy_filters import apply_filters
from app.core import SessionDep
from app.core.paginate import paginate_items
from app.schema.patient import PatientIn, PatientOut, StudyOut
from app.schema.patient import PatientPostOut,PatientDeleteIn,PatientStudyOut
from app.schema.patient import FilterSchema,field_model
from app.model import PatientModel
from app.model import StudyModel
from .. import utils

router = APIRouter()


sort_Query: str = Query(pattern="^(\+|\-)+")


@router.get("/hello")
async def hello_world():
    return "Hello World!"


@router.get("/")
def get_patient(session: SessionDep,
                sort: Annotated[str,sort_Query] = '+patient_id') -> Page[PatientOut]:
    sort_column = utils.get_sort_asc_desc(PatientModel, sort,PatientModel.patient_id)
    stmt = Select(PatientModel).filter(PatientModel.deleted_at.is_(None)).order_by(sort_column)
    print(stmt)
    patient_items_list, total, raw_params, params = paginate_items(session,stmt)
    response_list = []
    for patient_items in patient_items_list:
        patient = patient_items[0]
        response_list.append(PatientOut(patient_uid=patient.uid.hex,
                                        patient_id=patient.patient_id,
                                        gender=patient.gender,
                                        birth_date=patient.birth_date))
    page: Page[PatientOut] = create_page(response_list, total, params)
    return page


@router.post("/")
def post_patient(session: SessionDep,
                 patient_in_list: List[PatientIn],
                 ) -> PatientPostOut:
    data_list = []
    patient_out_list = []
    for patient_in in patient_in_list:
        patient_model = PatientModel(**patient_in.dict())
        data_list.append(patient_model)
    session.add_all(data_list)
    session.commit()
    for data in data_list:
        session.refresh(data)
        patient_out_list.append(PatientOut(patient_uid=data.uid.hex,
                                           patient_id=data.patient_id,
                                           gender=data.gender,
                                           birth_date=data.birth_date))
    patient_post_out = PatientPostOut(
        size=len(data_list),
        patient_out_list=patient_out_list)
    return patient_post_out


@router.delete("/")
def delete_patient(session: SessionDep,
                   patient_delelte_in_list: List[PatientDeleteIn],
                 ):
    for patient_delelte_in in patient_delelte_in_list:
        if patient_delelte_in.patient_uid or patient_delelte_in.patient_id:
            patient_model_list = session.query(PatientModel).filter(or_(PatientModel.uid == patient_delelte_in.patient_uid,
                                                                    PatientModel.patient_id == patient_delelte_in.patient_id
                                                                    )).all()
            for patient_model in patient_model_list:
                patient_model.deleted_at = datetime.datetime.now()
            session.commit()
    return "Delete Patient"


@router.post("/query/study")
def post_patient_study_query(session: SessionDep,
                 filter_schema:FilterSchema,
                 sort: Annotated[str,sort_Query] = '+patient_id'
                 ) -> Page[PatientStudyOut]:
    filter_ = filter_schema.dict()['filter_']
    # model_field_list = get_model_by_field(filter_)
    # print('model_field_list')
    # print(model_field_list)
    query = (session.query(PatientModel.uid.label('patient_uid'),
                           PatientModel.patient_id.label('patient_id'),
                           PatientModel.gender.label('gender'),
                           PatientModel.birth_date.label('birth_date'),
                           func.json_agg(func.json_build_object(text('\'study_uid\''),StudyModel.uid,
                                                                text('\'study_date\''),StudyModel.study_date,
                                                                text('\'study_time\''),StudyModel.study_time,
                                                                text('\'study_description\''),StudyModel.study_description,
                                                                text('\'accession_number\''),StudyModel.accession_number,
                                                                )).label('study_array_json'),
                           ).
             join(PatientModel, PatientModel.uid == StudyModel.patient_uid).
             group_by(PatientModel.uid, ).
             order_by(PatientModel.patient_id.desc()))
    print(query)
    items_list, total, raw_params, params = paginate_items(session, query)
    response_list = []
    for item in items_list:
        study_list = []
        for study_array in item.study_array_json:
            studyOut = StudyOut(**study_array)
            study_list.append(studyOut)
        patient_model = PatientStudyOut(patient_id = item.patient_id,
                                        gender     = item.gender,
                                        birth_date = item.birth_date,
                                        study = study_list
        )
        response_list.append(patient_model)
    print('response_list[0]')
    print(response_list[0])
    page: Page[PatientStudyOut] = create_page(response_list, total, params)
    print(type(page))
    return page
