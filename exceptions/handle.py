from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import ValidationError
# from pydantic_validation_decorator import FieldValidationError
from exceptions.exception import (
    AuthException,
    LoginException,
    ModelValidatorException,
    PermissionException,
    ServiceException,
    ServiceWarning,
)
# from utils.log_util import logger
# from utils.response_util import jsonable_encoder, JSONResponse, ResponseUtil
from datetime import datetime


def handle_exception(app: FastAPI):
    """
    全域異常處理
    """

    # 自訂token檢驗異常
    # @app.exception_handler(AuthException)
    # async def auth_exception_handler(request: Request, exc: AuthException):
    #     return ResponseUtil.unauthorized(data=exc.data, msg=exc.message)

    # 自訂登錄檢驗異常
    # @app.exception_handler(LoginException)
    # async def login_exception_handler(request: Request, exc: LoginException):
    #     return ResponseUtil.failure(data=exc.data, msg=exc.message)

    # 自訂模型檢驗異常
    # @app.exception_handler(ModelValidatorException)
    # async def model_validator_exception_handler(request: Request, exc: ModelValidatorException):
    #     return ResponseUtil.failure(data=exc.data, msg=exc.message)

    # 自訂欄位檢驗異常
    # @app.exception_handler(ValidationError)
    # async def field_validation_error_handler(request: Request, exc: FieldValidationError):
    #     logger.warning(exc.message)
    #     return ResponseUtil.failure(msg=exc.message)

    # 自訂許可權檢驗異常
    # @app.exception_handler(PermissionException)
    # async def permission_exception_handler(request: Request, exc: PermissionException):
    #     return ResponseUtil.forbidden(data=exc.data, msg=exc.message)

    # 自訂服務異常
    # @app.exception_handler(ServiceException)
    # async def service_exception_handler(request: Request, exc: ServiceException):
    #     logger.error(exc.message)
    #     return ResponseUtil.error(data=exc.data, msg=exc.message)

    # 自訂服務警告
    # @app.exception_handler(ServiceWarning)
    # async def service_warning_handler(request: Request, exc: ServiceWarning):
    #     logger.warning(exc.message)
    #     return ResponseUtil.failure(data=exc.data, msg=exc.message)

    # 處理其他http請求異常
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            content=jsonable_encoder({'code': exc.status_code, 'msg': exc.detail}), status_code=exc.status_code
        )

    # 處理其他異常
    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(str(exc)))
