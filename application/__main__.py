from enum import Enum

import uvicorn
from fastapi import FastAPI

from application.models import IviApiResponseResult
from application.service.elastic import ElasticWizard
from application.service.ivi_order import IviOrderManager

app = FastAPI()


class ContentTypeEnum(str, Enum):
    film = "film"
    serial = "serial"
    every = "*"


@app.get("/{content_type}/{film}")
async def get_film(film: str, content_type: ContentTypeEnum):
    result = await ElasticWizard.search_for_object(content_type, film)
    return {
        "content": [
            IviApiResponseResult(**item["_source"]).dict(include={"title", "object_type"})
            for item in result["hits"]["hits"]
        ]
    }


@app.post("/film/{film}")
async def post_film(film: str):
    try:
        response = await IviOrderManager.run(film)
    except Exception as error:
        return {"detail": str(error)}
    else:
        return response


if __name__ == "__main__":
    uvicorn.run(app, port=8080)
