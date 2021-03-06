from typing import Union

from aiohttp import ClientTimeout, BasicAuth
from pydantic import BaseSettings, validator, AnyHttpUrl, confloat

from application.models import IviApiResponseResult


class ELKSettings(BaseSettings):
    ELASTIC_HOST: str = "localhost"
    ELASTIC_PORT: str = "9200"
    IVI_INDEX: str = "/ivi"

    ELASTIC_IVI_PATH: Union[AnyHttpUrl, str] = None

    @validator("ELASTIC_IVI_PATH", pre=True)
    def elastic_ivi_path(cls, v, values) -> str:
        if v:
            return v
        return AnyHttpUrl.build(
            scheme="http",
            host=values["ELASTIC_HOST"],
            port=values["ELASTIC_PORT"],
            path=values["IVI_INDEX"]
        )

    ELASTIC_LOGIN: str = "elastic"
    ELASTIC_PASSWORD: str = "XOJvubwiaCVB5oeB9bLL"

    @property
    def elastic_auth(self) -> BasicAuth:
        return BasicAuth(self.ELASTIC_LOGIN, self.ELASTIC_PASSWORD)

    ELASTIC_SEARCH_TIE_BREAKER: confloat(ge=0.0, le=1.0) = 0.3


class HTTPSettings(BaseSettings):
    RAISE_FOR_STATUS: bool = True
    TIMEOUT: Union[float, ClientTimeout] = ClientTimeout(10)

    @validator("TIMEOUT")
    def timeout_to_correct_class(cls, v) -> ClientTimeout:
        if isinstance(v, ClientTimeout):
            return v
        return ClientTimeout(v)

    MAX_TRIES: int = 2
    MAX_TIME: int = 10

    USER_AGENT_SAMPLE: str = (
        "Mozilla/5.0 (Windows NT 6.4; WOW64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/41.0.2225.0 Safari/537.36 "
    )

    class Config(BaseSettings.Config):
        arbitrary_types_allowed = True


class IviSettings(BaseSettings):
    LIMIT: int = 10
    IVI_API_LINK: str = None

    @validator("IVI_API_LINK")
    def api_link(cls, v):
        if v:
            return v
        base_link = (
            "https://api.ivi.ru/mobileapi/autocomplete/common/v7/"
            "?query={name}"
            "&limit={limit}"
            "&app_version=870"
            "&object_type=content"
            "&fields="
        )
        return base_link + ",".join(IviApiResponseResult.__fields__.keys())


class Settings:
    elk: ELKSettings = ELKSettings()
    http: HTTPSettings = HTTPSettings()
    ivi: IviSettings = IviSettings()

