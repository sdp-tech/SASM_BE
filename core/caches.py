import traceback
import logging

from django.core.cache import cache


logger = logging.getLogger('django')


def get_cache(key_prefix, key_suffix_keyword):
    def wrapper(func):
        def decorator(*args, **kwargs):
            # cache key full name 구하기
            cache_key = key_prefix + str(kwargs[key_suffix_keyword])
            data = None
            try:
                # 주어진 key로 캐시 가져오기 시도
                data = cache.get(cache_key)
            except:
                # redis 동작 안함 등의 오류 처리
                logger.error(traceback.format_exc())

            # cache entry가 없거나 cache에 문제가 있는 경우, 본 함수 실행
            if data is None:
                data = func(*args, **kwargs)
                try:
                    # 캐시가 없는 경우, 캐시 엔트리 추가
                    cache.set(cache_key, data)
                except:
                    # redis 동작 안함 등의 오류 처리
                    logger.error(traceback.format_exc())

            return data
        return decorator
    return wrapper


def delete_cache(key_prefix, key_suffix_keyword):
    def wrapper(func):
        def decorator(*args, **kwargs):
            # cache key full name 구하기
            cache_key = key_prefix + str(kwargs[key_suffix_keyword].id)
            print(cache_key)
            data = func(*args, **kwargs)
            try:
                # 주어진 key에 대해 캐시 삭제
                cache.delete(cache_key)
            except:
                # redis 동작 안함 등의 오류 처리
                logger.error(traceback.format_exc())

            return data
        return decorator
    return wrapper
