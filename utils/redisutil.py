import logging
import redis
import traceback
from django.conf import settings


logger = logging.getLogger(__name__)


REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT
REDIS_DB = settings.REDIS_DB


def get_redis():
    x = redis.StrictRedis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
    )

    return x


def my_get(name):
    try:
        x = get_redis().get(name)
    except:
        logger.error(traceback.format_exc())
        x = None

    return x


def my_set(name, value):
    try:
        get_redis().set(name, value)
    except:
        logger.error(traceback.format_exc())
