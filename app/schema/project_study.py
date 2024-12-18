import datetime
import uuid
from typing import Any, List, Optional, Dict,Union
from pydantic import BaseModel


class ProjectStudyOutput(BaseModel):
    project_study_uid : Union[uuid.UUID,str]
    project_name      : Optional[str]
    patient_id        : Optional[str]
    gender            : Optional[str]
    study_date        : Optional[str]
    study_time        : Optional[str]
    study_description : Optional[str]
    accession_number  : Optional[str]
    extra_data        : Optional[Dict[str, Any]]
    class Config:
        extra = "ignore"

    # {'project_study_uid': UUID('57c436d7-c69d-4706-aa6f-735388500461'),
    # 'project_name': 'SHH_Task_seg_Test',
    # 'patient_id': '00001517',
    # 'gender': 'F', 'age': 74,
    # 'study_date': '2012-12-17',
    # 'study_time': '18:17:06',
    # 'study_description': 'Brain MRI , Stroke (-C)',
    # 'accession_number': '211217039',
    # 'extra_data': {}}


class ProjectStudyPost(BaseModel):
    project_uid    : Union[uuid.UUID,str]
    study_uid_list : List[Union[uuid.UUID,str]]
    class Config:
        extra = "ignore"


class ProjectStudyPost(BaseModel):
    project_uid    : Union[uuid.UUID,str]
    study_uid_list : List[Union[uuid.UUID,str]]
    class Config:
        extra = "ignore"


class ProjectStudyAccessionNumberPost(BaseModel):
    project_uid    : Union[uuid.UUID,str]
    accession_number_list : List[str]
    class Config:
        extra = "ignore"