import os
from typing import Union

from pydantic import BaseSettings, validator, AnyHttpUrl

ELASTIC_SEARCH_HOST = os.environ.get("ELASTIC_SEARCH_HOST", "127.0.0.1")
ELASTIC_SEARCH_PORT = os.environ.get("ELASTIC_SEARCH_HOST", "9200")
IVI_INDEX = "/ivi"


class ELKSettings(BaseSettings):
    ELASTIC_SEARCH_HOST: str = "localhost"
    ELASTIC_SEARCH_PORT: str = "9200"
    ELASTIC_IVI_PATH: Union[AnyHttpUrl, str] = None

    @validator("ELASTIC_IVI_PATH", pre=True)
    def elastic_ivi_path(cls, v, values) -> str:
        if v:
            return v
        return AnyHttpUrl.build(
            scheme="http",
            host=values["ELASTIC_SEARCH_HOST"],
            port=values["ELASTIC_SEARCH_PORT"],
            path=IVI_INDEX
        )


ELASTIC_IVI_PATH = ELKSettings().ELASTIC_IVI_PATH
