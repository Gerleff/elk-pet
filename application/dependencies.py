from functools import lru_cache

from aiohttp import ClientSession

from application.settings import Settings


@lru_cache(maxsize=None)
def get_aiohttp_client_session() -> ClientSession:
    return ClientSession(raise_for_status=Settings.http.RAISE_FOR_STATUS,
                         timeout=Settings.http.TIMEOUT)
