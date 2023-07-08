# rest_framework
from rest_framework.exceptions import APIException


class CustomException(APIException):
    def __init__(self, code: str, status_code: int, description: str):
        self.status_code = status_code  # needed for DRF to work
        self.detail = {
            "code": code,
            "status_code": status_code,
            "description": description,
        }

class LinkingException(CustomException):
    
    CODE = "LINKING_EXCEPTION"
    STATUS_CODE = 500
    DESCRIPTION = "Error linking data"

    def __init__(self, description = None):
        super().__init__(self.CODE, self.STATUS_CODE, description or self.DESCRIPTION)