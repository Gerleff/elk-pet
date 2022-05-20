import backoff
import fake_useragent
from loguru import logger

from application.dependencies import get_aiohttp_client_session
from application.settings import Settings


def get_external_api_headers():
    try:
        return {"User-Agent": fake_useragent.UserAgent().random}
    except IndexError as error:
        logger.warning(
            f"order: fake user agent error: {type(error)}: error"
        )
        return {"User-Agent": Settings.http.USER_AGENT_SAMPLE}


class HTTPClient:
    retry_policy = backoff.on_exception(
        backoff.expo,
        exception=BaseException,
        max_tries=Settings.http.MAX_TRIES,
        max_time=Settings.http.MAX_TIME,
    )

    @classmethod
    @retry_policy
    async def get(cls, url: str, **request_params):
        return await cls._request("GET", url, request_params)

    @classmethod
    @retry_policy
    async def post(cls, url: str, **request_params):
        return await cls._request("POST", url, request_params)

    @classmethod
    async def _request(cls, method: str, url: str, request_params: dict):
        async with get_aiohttp_client_session().request(method, url, **request_params) as response:
            return await response.json()
