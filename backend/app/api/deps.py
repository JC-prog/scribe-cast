from functools import lru_cache

from redis import Redis
from rq import Queue

from app.config import settings


@lru_cache
def get_redis_conn() -> Redis:
    return Redis.from_url(settings.redis_url)


def get_queue() -> Queue:
    return Queue(settings.queue_name, connection=get_redis_conn())
