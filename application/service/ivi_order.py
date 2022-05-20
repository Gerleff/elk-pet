from typing import Optional

from application.models import IviApiResponseResult, IviApiResponse
from application.service.elastic import ElasticWizard
from application.service.http import HTTPClient, get_external_api_headers
from application.settings import Settings

VID_TYPE_MAP = {"film": "Фильм", "serial": "Сериал"}


class IviOrderManager:
    api_limit = Settings.ivi.LIMIT

    @classmethod
    async def run(cls, message: str):
        api_link = Settings.ivi.IVI_API_LINK.format(name=message, limit=cls.api_limit)
        objects = await cls.send_request(api_link)
        already_have_titles = await cls.check_if_content_already_in_db(objects)
        titles = []
        for result in objects:
            await ElasticWizard.store_object(result)
            titles.append(result.title)
        return {"new": titles, "old": already_have_titles}

    @classmethod
    async def send_request(cls, api_link: str) -> Optional[list[IviApiResponseResult]]:
        ivi_response = await HTTPClient.get(api_link, headers=get_external_api_headers())
        return IviApiResponse(**ivi_response).result

    @classmethod
    async def check_if_content_already_in_db(cls, objects: list[IviApiResponseResult]) -> list[str]:
        result = await ElasticWizard.check_objects(objects)
        already_have_ids = {int(item["_id"]) for item in result["hits"]["hits"]}
        already_have_titles = []
        for obj in objects:
            if obj.id in already_have_ids:
                already_have_titles.append(f"{obj.title} ({obj.year_of_content})")
                objects.remove(obj)
        return already_have_titles
