import calendar
import re
from typing import List

from fastapi import APIRouter
from fastapi_pagination.api import create_page
from sqlalchemy_filters import apply_filters

from app.core import SessionDep
from app.core.paginate import paginate_items
from app.model.patient import PatientModel
from app.model.study import TextReportModel,TextReportRawModel,StudyModel
from app.schema import base as base_schema
from app.schema import text_report as text_report_schema
from ..utils import get_model_by_field,get_regexp,get_regexp_filter,get_orther_filter

router = APIRouter()

pattern_impression_str = re.compile(r'(?i:impression\s?:?|imp:?|conclusions?:?)')
pattern_depiction = re.compile(r'Summary :\n(.*)(\n.+)醫師', re.DOTALL)

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


def get_text_report(text_report_items_list: List):
    response_list = []
    for text_report_items in text_report_items_list:
        # text_report = text_report_items[0]
        text = text_report_items[-1]
        if text:
            impression = get_impression_by_text(text)
        else:
            text = ""
            impression = ""
        response_list.append(text_report_schema.TextReportOut(patient_id = text_report_items[0],
                                                              gender = text_report_items[1],
                                                              accession_number=text_report_items[2],
                                                              study_description = text_report_items[3],
                                                              text=text,
                                                              impression = impression
                                                   ))
    return response_list


@router.post("/query")
async def post_text_report_query(filter_schema : base_schema.FilterSchema,
                                 session: SessionDep) -> text_report_schema.TextReportPage[text_report_schema.TextReportOut]:
    filter_ = filter_schema.dict()['filter_']
    filter_ = get_model_by_field(filter_,text_report_schema.field_model)
    query = (session.query( PatientModel.patient_id,PatientModel.gender,
                            TextReportModel.accession_number,
                            StudyModel.study_description,
                            TextReportModel.text,).
             join(StudyModel,TextReportModel.accession_number==StudyModel.accession_number).
             join(PatientModel,StudyModel.patient_uid==PatientModel.uid))
    if len(filter_) > 0:
        orther_filter = list(filter(get_orther_filter, filter_))
        regexp_filter = list(filter(get_regexp_filter, filter_))
        print(regexp_filter)
        regexp_list = get_regexp(regexp_filter)
        filtered_query = apply_filters(query, orther_filter)
        filtered_query = filtered_query.filter(*regexp_list)
    else:
        filtered_query = query
    text_report_items_list, total, raw_params, params = paginate_items(session, filtered_query)
    response_list = get_text_report(text_report_items_list)

    page: text_report_schema.TextReportPage[text_report_schema.TextReportOut] = create_page(response_list, total, params)
    return page


# @router.post("/")
# async def post_text_report(,
#                                  session: SessionDep) -> text_report_schema.TextReportPage[text_report_schema.TextReportOut]:
#     print('filter_schema')
#     filter_ = filter_schema.dict()['filter_']
#     print('model_field_list')
#     query = session.query(TextReportRawModel)
#     orther_filter             = list(filter(lambda x: x['field'] != 'series_description', filter_))
#     filtered_query            = apply_filters(query, orther_filter)
#     print('filtered_query')
#     print(filtered_query)
#     print('filtered_query')
#
#     text_report_items_list, total, raw_params, params = paginate_items(session, filtered_query)
#     response_list = get_text_report(text_report_items_list)
#     #
#     page: text_report_schema.TextReportPage[text_report_schema.TextReportOut] = create_page(response_list, total, params)
#     return page
