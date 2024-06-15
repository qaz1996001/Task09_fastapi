import datetime
import uuid
from typing import Annotated, Union, Any, List

from fastapi import APIRouter, Depends, HTTPException,Body
from fastapi_pagination import Page,paginate
from fastapi_pagination.api import create_page
from sqlalchemy import and_, or_, any_, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import Select,func
from sqlalchemy_filters import apply_filters
from pydantic import BaseModel, Field

from app.core import SessionDep
from app.core.paginate import paginate_items
from app.model.study import StudyModel,TextReportModel
from app.model.patient import PatientModel
from app.model.series import SeriesModel
from .patient import PatientIn

router = APIRouter()


class StudyPostIn(BaseModel):
    patient_uid       : uuid.UUID
    study_date        : datetime.date
    study_time        : datetime.time
    study_description : str
    accession_number  : str


class StudyPatientPostIn(PatientIn):
    study_date        : datetime.date
    study_time        : datetime.time
    study_description : str
    accession_number  : str


class StudyOut(BaseModel):
    study_uid: str
    patient_uid: str
    patient_id: str
    gender: str
    study_date: datetime.date
    study_time: datetime.time
    study_description: str
    accession_number: str
    text: str


class StudySeriesOut(BaseModel):
    study_uid: str
    patient_uid: str
    study_date: datetime.date
    study_time: datetime.time
    study_description: str
    accession_number: str
    series_description: List[str]


class FilterItemSchema(BaseModel):
    field :str = Body('accession_number')
    op    :str = Body('eq')
    value :Any = Body('21301160043')


class FilterSchema(BaseModel):
    filter_ :List[FilterItemSchema] = Body(...)


@router.get("/hello")
async def hello_world():
    return "Hello World!"

field_model = dict(
    study_uid='StudyModel',
    patient_uid='PatientModel',
    patient_id='PatientModel',
    gender='PatientModel',
    study_date='StudyModel',
    study_time='StudyModel',
    study_description='StudyModel',
    accession_number='StudyModel',
    series='SeriesModel',
    text= 'TextReportModel'
)


def get_model_by_field(field_list):
    filter_field_list = list(filter(lambda x: field_model.get(x['field']) is not None, field_list))
    model_field_list = []
    for filter_field in filter_field_list:
        #  = list(map(lambda x: x['model'] = field_model.get(x['field'])) , filter_field_list))
        filter_field['model'] = field_model.get(filter_field['field'])
        model_field_list.append(filter_field)
    return model_field_list


def get_StudyOut(study_items_list):
    response_list = []
    for study_items in study_items_list:
        study = study_items[0]
        patient = study.patient
        text = study.text.text if study.text else ""
        response_list.append(StudyOut(study_uid=study.uid.hex,
                                      patient_uid=study.patient_uid.hex,
                                      patient_id=patient.patient_id,
                                      gender=patient.gender,
                                      study_date=study.study_date,
                                      study_time=study.study_time,
                                      study_description=study.study_description,
                                      accession_number=study.accession_number,
                                      text=text,
                                      ))
    return response_list


def get_StudySeriesOut(study_items_list):
    response_list = []
    for study_items in study_items_list:
        response_list.append(StudySeriesOut(study_uid=study_items.study_uid.hex,
                                            patient_uid=study_items.patient_uid.hex,
                                            study_date=study_items.study_date,
                                            study_time=study_items.study_time,
                                            study_description=study_items.study_description,
                                            accession_number=study_items.accession_number,
                                            series_description = study_items.series_description
                                            ))
    return response_list



@router.get("/")
def get_study(session: SessionDep) -> Page[StudyOut]:
    study_items_list, total, raw_params, params = paginate_items(session, Select(StudyModel))
    response_list        = get_StudyOut(study_items_list)
    page: Page[StudyOut] = create_page(response_list, total, params)
    return page



@router.post(path="/",
             summary = "patient 存在，加入study")
def post_study(session: SessionDep,
               study_postIn_list: List[StudyPostIn]):

    return ""


@router.post(path="/patient",
             summary = "patient 不存在，加入study"
             )
def post_study_patient(session: SessionDep,
                       study_patient_postIn_list: List[StudyPatientPostIn]):
    return ""


@router.post("/query")
def post_study_query(filter_schema : FilterSchema,
                 session: SessionDep) -> Page[StudyOut]:
    print('filter_schema')
    print(filter_schema.dict())
    study_items_list, total, raw_params, params = paginate_items(session, Select(StudyModel).order_by(StudyModel.study_date.desc()))
    response_list = get_StudyOut(study_items_list)

    page: Page[StudyOut] = create_page(response_list, total, params)
    return page



@router.post("/query/series")
async def post_study_series_query(filter_schema : FilterSchema,
                      session: SessionDep) -> Page[StudySeriesOut]:
    filter_ = filter_schema.dict()['filter_']
    model_field_list = get_model_by_field(filter_)
    print('model_field_list')
    print(model_field_list)
    query = (session.query(StudyModel.uid.label('study_uid'),
                           StudyModel.patient_uid.label('patient_uid'),
                           StudyModel.study_date.label('study_date'),
                           StudyModel.study_time.label('study_time'),
                           StudyModel.study_description.label('study_description'),
                           StudyModel.accession_number.label('accession_number'),
                           func.array_agg(SeriesModel.series_description).label('series_description'),
                           # func.json_agg(SeriesModel.series_description).label('series_description'),
                           ).
              join(PatientModel,StudyModel.patient_uid==PatientModel.uid).
             join(SeriesModel, StudyModel.uid == SeriesModel.study_uid).
             group_by(StudyModel.uid,).
             order_by(StudyModel.study_date.desc()))


    if len(filter_) > 0:
        series_description_filter = list(filter(lambda x: x['field'] == 'series_description', filter_))
        orther_filter             = list(filter(lambda x: x['field'] != 'series_description', filter_))
        filtered_query            = apply_filters(query, orther_filter)
        print(series_description_filter)
        print(orther_filter)
        q1 = filtered_query.cte('study_series')
        series_description_filter_sqlaichemy_ = list(
            map(lambda x: x['value'] == any_(func.cast(q1.c.series_description, ARRAY(Text))),
                series_description_filter))

        filtered_query = session.query(q1).filter(*series_description_filter_sqlaichemy_)
        print('filtered_query')
        print(filtered_query)
        print('filtered_query')
    else:
        filtered_query = query

    study_items_list, total, raw_params, params = paginate_items(session, filtered_query)
    response_list = get_StudySeriesOut(study_items_list)
    page: Page[StudySeriesOut] = create_page(response_list, total, params)
    return page