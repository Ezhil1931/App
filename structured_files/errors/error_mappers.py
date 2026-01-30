from errors.error_codes import ErrorCode, ErrorCodeStatus
from dtos.response_interfaces import APIResponse  # Assume this DTO exists
from constants.constants import HttpStatusCode  # Assume this exists

def map_error_code(api_response: APIResponse) -> APIResponse:
    if not api_response.errors or len(api_response.errors) == 0:
        api_response.code = HttpStatusCode.OK
        return api_response

    first_error_code = api_response.errors[0].code

    error_mapping = {
        ErrorCodeStatus[ErrorCode.MISSING_ENV_VARS]: HttpStatusCode.INTERNAL_SERVER_ERROR,
        ErrorCodeStatus[ErrorCode.USER_NOT_FOUND]: HttpStatusCode.NOT_FOUND,
        ErrorCodeStatus[ErrorCode.DATABASE_ERROR]: HttpStatusCode.CONFLICT,
        ErrorCodeStatus[ErrorCode.VALIDATION_ERROR]: HttpStatusCode.UNPROCESSABLE_ENTITY,
        ErrorCodeStatus[ErrorCode.WORK_ITEM_NOT_FOUND]: HttpStatusCode.NOT_FOUND,
        ErrorCodeStatus[ErrorCode.UNAUTHORIZED]: HttpStatusCode.UNAUTHORIZED,
        ErrorCodeStatus[ErrorCode.INTERNAL_SERVER_ERROR]: HttpStatusCode.INTERNAL_SERVER_ERROR,
    }

    api_response.code = error_mapping.get(first_error_code, HttpStatusCode.INTERNAL_SERVER_ERROR)
    return api_response