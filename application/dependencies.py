from functools import lru_cache

from aiohttp import ClientSession


@lru_cache(maxsize=None)
def get_aiohttp_client_session() -> ClientSession:
    return ClientSession()
