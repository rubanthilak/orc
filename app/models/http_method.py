from enum import Enum
from sqlalchemy import Column, Enum as SQLAlchemyEnum

class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"

HttpMethodEnum = SQLAlchemyEnum(HttpMethod)