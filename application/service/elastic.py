from application.models import IviApiResponseResult
from application.service.http import HTTPClient
from application.settings import Settings


class ElasticWizard:

    @classmethod
    async def store_object(cls, obj: IviApiResponseResult):
        result_json = obj.dict()
        _id = result_json.pop("id")
        await HTTPClient.post(f"{Settings.elk.ELASTIC_IVI_PATH}-{obj.object_type}/_doc/{_id}",
                              json=result_json,
                              auth=Settings.elk.elastic_auth)

    @classmethod
    async def check_objects(cls, objects: list[IviApiResponseResult]):
        return await HTTPClient.post(
                f"{Settings.elk.ELASTIC_IVI_PATH}-*/_search",
                json={
                    "query": {
                        "ids": {
                            "values": [item.id for item in objects]
                        }
                    },
                    "_source": False
                },
                auth=Settings.elk.elastic_auth,
        )

    @classmethod
    async def search_for_object(cls, content_type, film):
        return await HTTPClient.post(
                f"{Settings.elk.ELASTIC_IVI_PATH}-{content_type}/_search",
                json={
                    "query": {
                        "multi_match": {
                            "query": film,
                            "fields": ["title", "description"],
                            "tie_breaker": Settings.elk.ELASTIC_SEARCH_TIE_BREAKER
                        }
                    }
                },
                auth=Settings.elk.elastic_auth,
        )
