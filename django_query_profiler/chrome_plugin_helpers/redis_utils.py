"""
This module contains both functions of setting and getting from redis
Redis is used for storing the pickled query profiled data, and later to retrieve it back
"""
import pickle
import uuid
import os

import redis
from django.conf import settings

from django_query_profiler.query_profiler_storage import QueryProfiledData

REDIS_INSTANCE = redis.StrictRedis(
    host="redis",
    password="JguvU^FP4V",
    port=settings.DJANGO_QUERY_PROFILER_REDIS_PORT,
    db=settings.DJANGO_QUERY_PROFILER_REDIS_DB)


def store_data(query_profiled_data: QueryProfiledData, host: str) -> str:
    pickled_query_profiled_data = pickle.dumps(query_profiled_data)
    redis_key = str(uuid.uuid4().hex)
    ttl_seconds: int = settings.DJANGO_QUERY_PROFILER_REDIS_KEYS_EXPIRY_SECONDS
    REDIS_INSTANCE.hset(name = host + "_django_query_profiler", key= redis_key, value=pickled_query_profiled_data)
    return redis_key


def retrieve_data(redis_key: str, host : str) -> QueryProfiledData:
    redis_object = REDIS_INSTANCE.hget(host + "_django_query_profiler", redis_key)
    return pickle.loads(redis_object)

def get_host(request) -> str:
    host = request.headers.get('Host',"")
    host = host.split(".")
    host = host[0] if host else "localhost"
    return host

def clear_redis(host):
    REDIS_INSTANCE.delete(host + "_django_query_profiler")
