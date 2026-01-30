class ErrorCode:
    MISSING_ENV_VARS = "MissingEnvVarsErrorCode"
    USER_NOT_FOUND = "UserNotFoundErrorCode"
    INVALID_JSON_FORMAT = "InvalidJSONFormatErrorCode"
    VALIDATION_ERROR = "ValidationErrorCode"
    INTERNAL_SERVER_ERROR = "InternalServerErrorCode"
    DATABASE_ERROR = "DatabaseErrorErrorCode"
    UNAUTHORIZED = "UnauthorizedErrorCode"
    WORK_ITEM_NOT_FOUND = "WorkItemNotFoundErrorCode"
    ESCALATE_TO_LANE = "EscalateToLaneErrorCode"
    NO_ROWS_AFFECTED = "NoRowsAffectedErrorCode"
    SERIALIZE_EVENT_DATA = "SerializeEventDataErrorCode"
    COMMIT_TRANSACTION = "CommitTransactionErrorCode"
    EXTERNAL_API_FAILED = "ExternalApiFailed"


ErrorCodeStatus = {
    ErrorCode.MISSING_ENV_VARS: "CM_ENV_001",
    ErrorCode.USER_NOT_FOUND: "CM_SQL_002",
    ErrorCode.INVALID_JSON_FORMAT: "CM_ENV_003",
    ErrorCode.VALIDATION_ERROR: "CM_VAL_004",
    ErrorCode.INTERNAL_SERVER_ERROR: "CM_SQL_005",
    ErrorCode.DATABASE_ERROR: "CM_SQL_006",
    ErrorCode.UNAUTHORIZED: "CM_AUTH_007",
    ErrorCode.WORK_ITEM_NOT_FOUND: "CM_SQL_008",
    ErrorCode.NO_ROWS_AFFECTED: "CM_SQL_009",
    ErrorCode.SERIALIZE_EVENT_DATA: "CM_SER_001",
    ErrorCode.COMMIT_TRANSACTION: "CM_SQL_008",
    ErrorCode.EXTERNAL_API_FAILED: "CM_EX_001"
}
