import calendar
import re
from typing import List

from fastapi import APIRouter
from fastapi_pagination.api import create_page
from sqlalchemy_filters import apply_filters

from app.core import SessionDep
from app.core.paginate import paginate_items
from app.model.study import TextReportModel,TextReportRawModel
from app.schema import base as base_schema
from app.schema import text_report as text_report_schema

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


def get_text_report(text_report_items_list: List[TextReportRawModel]):
    response_list = []
    for text_report_items in text_report_items_list:
        text_report = text_report_items[0]
        if text_report.text:
            text = text_report.text
            impression = get_impression_by_text(text)
        else:
            text = ""
            impression = ""
        response_list.append(text_report_schema.TextReportOut(
                                                   accession_number=text_report.accession_number,
                                                   text=text,
                                                   impression = impression
                                                   ))
    return response_list


@router.post("/query")
async def post_text_report_query(filter_schema : base_schema.FilterSchema,
                                 session: SessionDep) -> text_report_schema.TextReportPage[text_report_schema.TextReportOut]:
    print('filter_schema')
    filter_ = filter_schema.dict()['filter_']
    print('model_field_list')
    query = session.query(TextReportRawModel)
    orther_filter             = list(filter(lambda x: x['field'] != 'series_description', filter_))
    filtered_query            = apply_filters(query, orther_filter)
    print('filtered_query')
    print(filtered_query)
    print('filtered_query')

    text_report_items_list, total, raw_params, params = paginate_items(session, filtered_query)
    response_list = get_text_report(text_report_items_list)
    #
    page: text_report_schema.TextReportPage[text_report_schema.TextReportOut] = create_page(response_list, total, params)
    return page

