from typing import Optional

import backoff
import fake_useragent  # noqa
from aiohttp import BasicAuth

from loguru import logger  # ToDO logstash?

from application.dependencies import get_aiohttp_client_session
from application.models import IviApiResponseResult, IviApiResponse
from application.settings import ELASTIC_IVI_PATH
from application.text import ivi_api_link

VID_TYPE_MAP = {"film": "Фильм", "serial": "Сериал"}


class IviOrderManager:
    max_tries = 2
    max_time = 10
    api_limit = 10
    user_agent_sample = (
        "Mozilla/5.0 (Windows NT 6.4; WOW64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/41.0.2225.0 Safari/537.36 "
    )
    retry_policy = backoff.on_exception(
        backoff.expo,
        exception=BaseException,
        max_tries=max_tries,
        max_time=max_time,
    )

    @classmethod
    async def run(cls, message: str):
        api_link = ivi_api_link.format(name=message, limit=cls.api_limit)
        objects = await cls.send_request(api_link)
        already_have_titles = await cls.check_if_content_already_in_db(objects)
        titles = []
        for result in objects:
            # vid_type = VID_TYPE_MAP[result.object_type]
            result_json = result.dict()
            _id = result_json.pop("id")
            async with get_aiohttp_client_session().post(
                    f"{ELASTIC_IVI_PATH}-{result.object_type}/_doc/{_id}",
                    json=result_json,
                    auth=BasicAuth("elastic", "XOJvubwiaCVB5oeB9bLL"),
            ) as es_res:
                logger.info(await es_res.json())
            titles.append(result.title)
        return {"new": titles, "old": already_have_titles}

    @classmethod
    @retry_policy
    async def send_request(cls, api_link: str) -> Optional[list[IviApiResponseResult]]:
        async with get_aiohttp_client_session().get(api_link, headers=cls._get_headers()) as response:
            response.raise_for_status()
            response_json = await response.json()
            return IviApiResponse(**response_json).result

    @classmethod
    def _get_headers(cls) -> dict:
        try:
            return {"User-Agent": fake_useragent.UserAgent().random}
        except IndexError as error:
            logger.warning(
                f"order: fake user agent error: {type(error)}: error"
            )
            return {"User-Agent": cls.user_agent_sample}

    @classmethod
    @retry_policy
    async def check_if_content_already_in_db(cls, objects: list[IviApiResponseResult]) -> list[str]:
        async with get_aiohttp_client_session().post(
                f"{ELASTIC_IVI_PATH}-*/_search",
                json={
                    "query": {
                        "ids": {
                            "values": [item.id for item in objects]
                        }
                    },
                    "_source": False
                },
                auth=BasicAuth("elastic", "XOJvubwiaCVB5oeB9bLL"),
        ) as es_res:
            result = await es_res.json()
            logger.info(f"check in db: {result}")
        already_have_ids = [int(item["_id"]) for item in result["hits"]["hits"]]
        logger.info(f"{already_have_ids = }")
        already_have_titles = []
        for obj in objects:
            if obj.id in already_have_ids:
                already_have_titles.append(f"{obj.title} ({obj.year_of_content})")
                objects.remove(obj)
        return already_have_titles
