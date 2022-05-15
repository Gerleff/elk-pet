import asyncio
from typing import Optional
import fake_useragent  # noqa
from aiohttp import BasicAuth

from loguru import logger  # ToDO logstash?

from application.dependencies import get_aiohttp_client_session
from application.models import IviApiResponseResult, IviApiResponse
from application.settings import ELASTIC_IVI_PATH
from application.text import ivi_api_link

VID_TYPE_MAP = {"film": "Фильм", "serial": "Сериал"}


class IviOrderManager:
    attempts_amount = 2
    timeout_duration = 5
    api_limit = 10
    user_agent_sample = (
        "Mozilla/5.0 (Windows NT 6.4; WOW64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/41.0.2225.0 Safari/537.36 "
    )

    def __init__(self, message: str):
        self.message = message
        self.api_link = ivi_api_link.format(name=message, limit=self.api_limit)
        self.session = get_aiohttp_client_session()

    async def run(self):
        objects = await self.send_request()
        already_have_titles = await self.check_if_content_already_in_db(objects)
        titles = []
        for result in objects:
            # vid_type = VID_TYPE_MAP[result.object_type]
            result_json = result.dict()
            _id = result_json.pop("id")
            async with self.session.post(
                    f"{ELASTIC_IVI_PATH}-{result.object_type}/_doc/{_id}",
                    json=result_json,
                    auth=BasicAuth("elastic", "XOJvubwiaCVB5oeB9bLL"),
            ) as es_res:
                logger.info(await es_res.json())
            titles.append(result.title)
        return {"new": titles, "old": already_have_titles}

    async def send_request(self) -> Optional[list[IviApiResponseResult]]:
        for counter in range(self.attempts_amount):
            try:
                try:
                    headers = {"User-Agent": fake_useragent.UserAgent().random}
                except IndexError as error:
                    logger.warning(
                        f"order: fake user agent error: {type(error)}: error"
                    )
                    headers = {"User-Agent": self.user_agent_sample}

                async with self.session.get(
                        self.api_link, headers=headers
                ) as response:
                    assert response.status == 200
                    response_json = await response.json()
                    return IviApiResponse(**response_json).result
            except AssertionError:
                await asyncio.sleep(self.timeout_duration)
                if counter == self.attempts_amount - 1:
                    logger.warning(f"Failure. Code {response.status}")
                    return []
            except ValueError as error:
                logger.error(str(error))
                return []
            except Exception as error:
                logger.warning(
                    f"order: request: unknown error: {type(error)} {error}"
                )

    async def check_if_content_already_in_db(self, objects: list[IviApiResponseResult]) -> list[str]:
        async with self.session.post(
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
        for obj in objects[:]:
            if obj.id in already_have_ids:
                already_have_titles.append(f"{obj.title} ({obj.get_year_of_content()})")
                objects.remove(obj)
        return already_have_titles
