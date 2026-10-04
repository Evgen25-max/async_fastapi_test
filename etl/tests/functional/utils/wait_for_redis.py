import os
import time

import redis

if __name__ == '__main__':
    redis_host = os.getenv('REDIS_HOST', 'redis')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    redis_password = os.getenv('REDIS_PASSW', '')

    print(f'Waiting for Redis at {redis_host}:{redis_port}...')

    while True:
        try:
            r = redis.Redis(host=redis_host, port=redis_port, password=redis_password)
            if r.ping():
                print('Redis is ready!')
                break
        except redis.exceptions.ConnectionError:
            pass
        time.sleep(2)
