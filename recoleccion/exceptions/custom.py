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

    def __str__(self):
        info = "\n"
        for key, value in self.detail.items():
            if key != "extra_details":
                info += f"{key}: {value}\n"
            else:
                if value:
                    info += f"{key}:\n"
                    for key, value in value.items():
                        info += f"\t{key}: {value}\n"
        return info


class LinkingException(CustomException):
    CODE = "LINKING_EXCEPTION"
    STATUS_CODE = 400
    DESCRIPTION = "Error linking data"

    def __init__(self, description=None):
        super().__init__(self.CODE, self.STATUS_CODE, description or self.DESCRIPTION)


class IncompatibleLinkingDatasets(LinkingException):
    CODE = "INCOMPATIBLE_LINKING_DATASETS"
    STATUS_CODE = 400
    DESCRIPTION = "The datasets seem to be too different to be linked"


class SenateLoadingException(CustomException):
    CODE = "SENATE_LOADING_EXCEPTION"
    STATUS_CODE = 500
    DESCRIPTION = "Error loading senate data"

    def __init__(self, description=None):
        super().__init__(self.CODE, self.STATUS_CODE, description or self.DESCRIPTION)


class DeputiesLoadingException(CustomException):
    CODE = "DEPUTIES_LOADING_EXCEPTION"
    STATUS_CODE = 400
    DESCRIPTION = "Error loading deputies data"

    def __init__(self, description=None):
        super().__init__(self.CODE, self.STATUS_CODE, description or self.DESCRIPTION)


class PageNotFound(CustomException):
    CODE = "PAGE_NOT_FOUND"
    STATUS_CODE = 404
    DESCRIPTION = "Page not found"

    def __init__(self, description=None):
        super().__init__(self.CODE, self.STATUS_CODE, description or self.DESCRIPTION)


class TextSummarizerException(CustomException):
    CODE = "TEXT_SUMMARIZER_EXCEPTION"
    STATUS_CODE = 400
    DESCRIPTION = "Error summarizing text"

    def __init__(self, description=None):
        super().__init__(self.CODE, self.STATUS_CODE, description or self.DESCRIPTION)


class EmptyProjectText(CustomException):
    CODE = "EMPTY_PROJECT_TEXT"
    STATUS_CODE = 400
    DESCRIPTION = "The project text is empty"

    def __init__(self, project_id: int):
        description = f"The project with id {project_id} has no text"
        super().__init__(self.CODE, self.STATUS_CODE, description)
