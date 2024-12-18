import calendar
import re
from typing import Annotated, Union, Any, List

from fastapi import APIRouter
from fastapi_pagination import Page,paginate
from fastapi_pagination.api import create_page
from sqlalchemy import and_, or_, any_, Text,exists,literal_column,select
from sqlalchemy.dialects.postgresql import array,ARRAY
from sqlalchemy.sql import func
from sqlalchemy_filters import apply_filters

from app.core import SessionDep
from app.core.paginate import paginate_items
from app.model.study import StudyModel,TextReportModel
from app.model.patient import PatientModel
from app.model.series import SeriesModel
from app.schema import study as study_schema
from app.schema import base as base_schema
from ..utils import get_model_by_field




pattern_impression_str = re.compile(r'(?i:impression\s?:?|imp:?|conclusions?:?)')
pattern_depiction = re.compile(r'Summary :\n(.*)(\n.+)醫師', re.DOTALL)


def get_impression_by_text(x):
    global pattern_depiction,pattern_impression_str
    depiction_match = pattern_depiction.search(x)
    if depiction_match:
        depiction = depiction_match.group(1)
        result_impression_str = pattern_impression_str.split(depiction)
        if len(result_impression_str) > 0:
            return result_impression_str[-1]
        else:
            return ''


def get_StudyOut(study_items_list):
    response_list = []
    for study_items in study_items_list:
        study = study_items[0]
        patient = study.patient
        if study.text:
            text = study.text.text
            impression = get_impression_by_text(text)
        else:
            text = ""
            impression = ""

        response_list.append(study_schema.StudyOut(study_uid=study.uid.hex,
                                                   patient_uid=study.patient_uid.hex,
                                                   patient_id=patient.patient_id,
                                                   gender=patient.gender,
                                                   study_date=study.study_date,
                                                   study_time=study.study_time,
                                                   study_description=study.study_description,
                                                   accession_number=study.accession_number,
                                                   text=text,
                                                   impression = impression
                                                   ))
    return response_list



def get_StudySeriesOut(study_items_list):
    response_list = []
    series_description_set = set()
    for study_items in study_items_list:
        response_list.append(study_schema.StudySeriesOut(study_uid=study_items.study_uid.hex,
                                                         patient_uid=study_items.patient_uid.hex,
                                                         study_date=study_items.study_date,
                                                         study_time=study_items.study_time,
                                                         study_description=study_items.study_description,
                                                         accession_number=study_items.accession_number,
                                                         series_description = study_items.series_description
                                            ))
        series_description_set.update(study_items.series_description)
    return response_list,series_description_set


def get_StudySeriesOut2(study_items_list):
    response_list = []
    series_description_set = set()
    for study_items in study_items_list:
        age = get_age_by_study_date(study_items.birth_date,study_items.study_date)
        series_description = list (map(lambda x:{x:1},study_items.series_description))
        response_list.append(study_schema.StudySeriesOut2(patient_id=study_items.patient_id,
                                                          gender=study_items.gender,
                                                          age=age,
                                                          study_date=study_items.study_date,
                                                          study_time=study_items.study_time,
                                                          study_description=study_items.study_description,
                                                          accession_number=study_items.accession_number,
                                                          series_description = series_description,
                                            ))
        series_description_set.update(study_items.series_description)
    return response_list,series_description_set


def get_age_by_study_date(birth_date, study_date):
        year = study_date.year - birth_date.year
        month = study_date.month - birth_date.month
        if month < 0:
            year = year - 1
            month = 12 + month
        day_list = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if calendar.isleap(study_date.year):  # 判斷如果是閏年
            day_list[1] = 29  # 就將二月份的天數改成 29 天
        day = study_date.day - birth_date.day
        if day < 0:
            month = month - 1
            if month < 0:
                year = year - 1
                month = 12 + month
            day = day_list[month] + day
        return f'{year}Y{month}M'


router = APIRouter()


@router.get("/hello")
async def hello_world():
    return "Hello World!"



@router.get("/")
def get_study(session: SessionDep) -> Page[study_schema.StudyOut]:
    study_items_list, total, raw_params, params = paginate_items(session, select(StudyModel))
    response_list        = get_StudyOut(study_items_list)
    page: Page[study_schema.StudyOut] = create_page(response_list, total, params)
    return page



@router.post(path="/",
             summary = "patient 存在，加入study")
async def post_study(session: SessionDep,
                     study_postIn_list: List[study_schema.StudyPostIn]):

    return ""


@router.post(path="/patient",
             summary = "patient 不存在，加入study"
             )
async def post_study_patient(session: SessionDep,
                       study_patient_postIn_list: List[study_schema.StudyPatientPostIn]):
    return ""


@router.post("/query")
async def post_study_query(filter_schema : study_schema.FilterSchema,
                 session: SessionDep) -> Page[study_schema.StudyOut]:
    print('filter_schema')
    filter_ = filter_schema.dict()['filter_']
    model_field_list = get_model_by_field(filter_,study_schema.field_model)
    print('model_field_list')
    print(model_field_list)
    query = (session.query(StudyModel).
             join(PatientModel, StudyModel.patient_uid == PatientModel.uid).
             join(TextReportModel, StudyModel.accession_number == TextReportModel.accession_number,isouter=True).
             group_by(StudyModel.uid, ).
             order_by(StudyModel.study_date.desc()))
    if len(model_field_list) > 0:
        orther_filter             = list(filter(lambda x: x['field'] != 'series_description', filter_))
        filtered_query            = apply_filters(query, orther_filter)
        print('filtered_query')
        print(filtered_query)
        print('filtered_query')
    else:
        filtered_query = query

    study_items_list, total, raw_params, params = paginate_items(session, filtered_query)
    response_list = get_StudyOut(study_items_list)

    page: Page[study_schema.StudyOut] = create_page(response_list, total, params)
    return page



@router.post("/query/series")
async def post_study_series_query(filter_schema : study_schema.FilterSchema,
                      session: SessionDep) -> study_schema.StudySeriesGroupPage[study_schema.StudySeriesOut2]:
    filter_ = filter_schema.dict()['filter_']
    filter_ = get_model_by_field(filter_,study_schema.field_model)
    print('filter_',filter_)
    query = (session.query(StudyModel.uid.label('study_uid'),
                           StudyModel.patient_uid.label('patient_uid'),
                           PatientModel.patient_id.label('patient_id'),
                           PatientModel.gender.label('gender'),
                           PatientModel.birth_date.label('birth_date'),
                           StudyModel.study_date.label('study_date'),
                           StudyModel.study_time.label('study_time'),
                           StudyModel.study_description.label('study_description'),
                           StudyModel.accession_number.label('accession_number'),
                           func.array_agg(SeriesModel.series_description).label('series_description'),
                           ).
              join(PatientModel,StudyModel.patient_uid==PatientModel.uid).
             join(SeriesModel, StudyModel.uid == SeriesModel.study_uid).
             group_by(StudyModel.uid,
                      PatientModel.uid,
                      PatientModel.patient_id,
                      PatientModel.gender,
                      PatientModel.birth_date,
                      StudyModel.study_date,
                      StudyModel.study_time,
                      StudyModel.study_description,
                      StudyModel.accession_number).
             order_by(StudyModel.study_date.desc()))


    if len(filter_) > 0:
        series_description_filter = list(filter(lambda x: x['field'] == 'series_description', filter_))
        # orther_filter             = list(filter(lambda x: x['field'] != 'series_description', filter_))
        orther_filter             = list(filter(get_orther_filter, filter_))
        filtered_query            = apply_filters(query, orther_filter)
        study_series_cte  = filtered_query.cte('study_series')
        series_description_filter_sqlaichemy_ = list(map(lambda x: or_(literal_column('series_desc').like(x['value'])),series_description_filter))
        filtered_query = session.query(study_series_cte).filter(
            exists(
                select(1)
                .select_from(func.unnest(study_series_cte.c.series_description).alias('series_desc'))
                .where(*series_description_filter_sqlaichemy_)))
    else:
        filtered_query = query

    print('filtered_query', filtered_query)

    study_items_list, total, raw_params, params = paginate_items(session, filtered_query)
    response_list, series_description_set = get_StudySeriesOut2(study_items_list)
    series_description_group_key = base_schema.get_group_key_by_series(list(series_description_set))
    series_description_group_key['general_keys'] = [ 'patient_id',
                                                     'gender',
                                                     'age',
                                                     'study_date',
                                                     'study_time',
                                                     'study_description',
                                                     'accession_number',]
    additional_data = dict(series_description = sorted(series_description_set,
                                                       key=lambda x: base_schema.series_structure_sort.get(x, 999)),
                           group_key = series_description_group_key
                           )
    page: study_schema.StudySeriesGroupPage[study_schema.StudySeriesOut] = create_page(response_list,
                                                                                       total= total,
                                                                                       params=params,
                                                                                       **additional_data)
    return page


# @router.post("/query/series/download")
# async def post_study_series_query(filter_schema : study_schema.FilterSchema,
#                       session: SessionDep):
#     filter_ = filter_schema.dict()['filter_']
#     model_field_list = get_model_by_field(filter_)
#     query = (session.query(StudyModel.uid.label('study_uid'),
#                            StudyModel.patient_uid.label('patient_uid'),
#                            PatientModel.patient_id.label('patient_id'),
#                            PatientModel.gender.label('gender'),
#                            PatientModel.birth_date.label('birth_date'),
#                            StudyModel.study_date.label('study_date'),
#                            StudyModel.study_time.label('study_time'),
#                            StudyModel.study_description.label('study_description'),
#                            StudyModel.accession_number.label('accession_number'),
#                            func.array_agg(SeriesModel.series_description).label('series_description'),
#                            ).
#               join(PatientModel,StudyModel.patient_uid==PatientModel.uid).
#              join(SeriesModel, StudyModel.uid == SeriesModel.study_uid).
#              group_by(StudyModel.uid,
#                       PatientModel.uid,
#                       PatientModel.patient_id,
#                       PatientModel.gender,
#                       PatientModel.birth_date,
#                       StudyModel.study_date,
#                       StudyModel.study_time,
#                       StudyModel.study_description,
#                       StudyModel.accession_number).
#              order_by(StudyModel.study_date.desc()))
#
#
#     if len(model_field_list) > 0:
#         series_description_filter = list(filter(lambda x: x['field'] == 'series_description', filter_))
#         orther_filter             = list(filter(lambda x: x['field'] != 'series_description', filter_))
#         filtered_query            = apply_filters(query, orther_filter)
#
#         q1 = filtered_query.cte('study_series')
#         series_description_filter_sqlaichemy_ = list(
#             map(lambda x: x['value'] == any_(func.cast(q1.c.series_description, ARRAY(Text))),
#                 series_description_filter))
#
#         filtered_query = session.query(q1).filter(*series_description_filter_sqlaichemy_)
#     else:
#         filtered_query = query
#
#     response_list = session.execute(filtered_query).all()
#     total = len(response_list)
#     response_list, series_description_set = get_StudySeriesOut2(response_list)
#     series_description_group_key = base_schema.get_group_key_by_series(list(series_description_set))
#     series_description_group_key['general_keys'] = [ 'patient_id',
#                                                      'gender',
#                                                      'age',
#                                                      'study_date',
#                                                      'study_time',
#                                                      'study_description',
#                                                      'accession_number',]
#
#     additional_data = dict(series_description = sorted(series_description_set,
#                                                        key=lambda x: base_schema.series_structure_sort.get(x, 999)),
#                            group_key = series_description_group_key
#                            )
#     key_list = []
#     key_list.extend(series_description_group_key['general_keys'])
#     key_list.extend(series_description_group_key['structure_keys'])
#     key_list.extend(series_description_group_key['special_keys'])
#     key_list.extend(series_description_group_key['perfusion_keys'])
#     key_list.extend(series_description_group_key['functional_keys'])
#     response_dict = dict(
#         items = response_list,
#         total = total,
#         key   = key_list
#     )
#     response_dict.update(additional_data)
#     return response_dict

@router.post("/query/series/download")
async def post_study_series_query(filter_schema : study_schema.FilterSchema,
                      session: SessionDep):

    filter_ = filter_schema.dict()['filter_']
    model_field_list = get_model_by_field(filter_,study_schema.field_model)
    print('filter_',filter_)
    print('model_field_list', model_field_list)
    query = (session.query(StudyModel.uid.label('study_uid'),
                           StudyModel.patient_uid.label('patient_uid'),
                           PatientModel.patient_id.label('patient_id'),
                           PatientModel.gender.label('gender'),
                           PatientModel.birth_date.label('birth_date'),
                           StudyModel.study_date.label('study_date'),
                           StudyModel.study_time.label('study_time'),
                           StudyModel.study_description.label('study_description'),
                           StudyModel.accession_number.label('accession_number'),
                           func.array_agg(SeriesModel.series_description).label('series_description'),
                           ).
              join(PatientModel,StudyModel.patient_uid==PatientModel.uid).
             join(SeriesModel, StudyModel.uid == SeriesModel.study_uid).
             group_by(StudyModel.uid,
                      PatientModel.uid,
                      PatientModel.patient_id,
                      PatientModel.gender,
                      PatientModel.birth_date,
                      StudyModel.study_date,
                      StudyModel.study_time,
                      StudyModel.study_description,
                      StudyModel.accession_number).
             order_by(StudyModel.study_date.desc()))

    if len(model_field_list) > 0:
        series_description_filter = list(filter(lambda x: x['field'] == 'series_description', filter_))
        orther_filter             = list(filter(lambda x: x['field'] != 'series_description', filter_))
        filtered_query            = apply_filters(query, orther_filter)
        study_series_cte  = filtered_query.cte('study_series')
        series_description_filter_sqlaichemy_ = list(map(lambda x: or_(literal_column('series_desc').like(x['value'])),series_description_filter))
        filtered_query = session.query(study_series_cte).filter(
            exists(
                select(1)
                .select_from(func.unnest(study_series_cte.c.series_description).alias('series_desc'))
                .where(*series_description_filter_sqlaichemy_)))
    else:
        filtered_query = query

    print('filtered_query', filtered_query)

    response_list = session.execute(filtered_query).all()
    total = len(response_list)
    response_list, series_description_set = get_StudySeriesOut2(response_list)
    series_description_group_key = base_schema.get_group_key_by_series(list(series_description_set))
    series_description_group_key['general_keys'] = [ 'patient_id',
                                                     'gender',
                                                     'age',
                                                     'study_date',
                                                     'study_time',
                                                     'study_description',
                                                     'accession_number',]

    additional_data = dict(series_description = sorted(series_description_set,
                                                       key=lambda x: base_schema.series_structure_sort.get(x, 999)),
                           group_key = series_description_group_key
                           )
    key_list = []
    key_list.extend(series_description_group_key['general_keys'])
    key_list.extend(series_description_group_key['structure_keys'])
    key_list.extend(series_description_group_key['special_keys'])
    key_list.extend(series_description_group_key['perfusion_keys'])
    key_list.extend(series_description_group_key['functional_keys'])
    response_dict = dict(
        items = response_list,
        total = total,
        key   = key_list
    )
    response_dict.update(additional_data)
    return response_dict
