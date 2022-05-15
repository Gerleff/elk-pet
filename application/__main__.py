from enum import Enum

import uvicorn
from aiohttp import BasicAuth
from fastapi import FastAPI
from loguru import logger

from application.dependencies import get_aiohttp_client_session
from application.models import IviApiResponseResult
from application.service import IviOrderManager
from application.settings import ELASTIC_IVI_PATH

app = FastAPI()


class ContentTypeEnum(str, Enum):
    film = "film"
    serial = "serial"
    every = "*"


@app.get("/{content_type}/{film}")
async def get_film(film: str, content_type: ContentTypeEnum):
    async with get_aiohttp_client_session().post(
        f"{ELASTIC_IVI_PATH}-{content_type}/_search",
        json={
            "query": {
                "multi_match": {
                    "query": film,
                    "fields": ["title", "description"],
                }
            }
        },
        auth=BasicAuth("elastic", "XOJvubwiaCVB5oeB9bLL"),
    ) as es_res:
        result = await es_res.json()
        logger.info(result)
    return {
        "content": [
            IviApiResponseResult(**item["_source"]).dict(include={"title", "object_type"})
            for item in result["hits"]["hits"]
            # if item["_score"] > 0.5
        ]
    }


@app.post("/film/{film}")
async def post_film(film: str):
    try:
        response = await IviOrderManager(film).run()
    except Exception as error:
        return {"detail": str(error)}
    else:
        return response


if __name__ == "__main__":
    uvicorn.run(app, port=8080)
