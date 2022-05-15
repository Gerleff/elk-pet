from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, validator


class PosterType(str, Enum):
    VERTICAL = "poster-vertical"
    HORIZONTAL = "poster-horizontal"


class IviPoster(BaseModel):
    width: int
    height: int
    content_format: str
    url: str
    id: int
    type: PosterType


OBJECT_TYPE_MAP = {"video": "film", "compilation": "serial"}


class IviApiResponseResult(BaseModel):
    object_type: Optional[str]
    year: Optional[str]
    years: Optional[list[int]]
    title: Optional[str]
    description: Optional[str]
    synopsis: Optional[str]
    genres: Optional[list[int]]
    categories: Optional[list[int]]
    id: Optional[int]
    kp_id: Optional[str]
    kp_rating: Optional[str]
    imdb_rating: Optional[str]
    ivi_rating_10: Optional[str]
    posters: Optional[list[IviPoster]]
    share_link: Optional[str]

    @validator("object_type")
    def change_type_name(cls, _type):
        return OBJECT_TYPE_MAP.get(_type) or _type

    @property
    def poster_url(self) -> Optional[str]:
        if posters := self.posters:
            return posters[0].url
        return "http://n_a.ru"

    def get_year_of_content(self) -> Union[str, int]:
        if year := self.year:
            return year
        year_from, year_to = min(self.years), max(self.years)
        if year_from == year_to:
            return year_from
        return f"{year_from} - {year_to}"


class IviApiResponse(BaseModel):
    result: list[IviApiResponseResult]

    @validator("result", pre=True)
    def check_if_results_exist(cls, result):
        for obj in result.copy():
            if obj.get("object_type") not in OBJECT_TYPE_MAP.keys():
                result.remove(obj)
        if not result:
            raise ValueError("Results not found!")
        return result
