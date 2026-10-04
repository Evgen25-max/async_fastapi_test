import os
import time
from elasticsearch import Elasticsearch

if __name__ == '__main__':
    elastic_host = os.getenv('ELASTIC_HOST', 'elasticsearch')
    elastic_port = int(os.getenv('ELASTIC_PORT', 9200))
    elastic_schema = os.getenv('ELASTIC_SCHEMA', 'http://')

    es_url = f"{elastic_schema}{elastic_host}:{elastic_port}"
    es_client = Elasticsearch(hosts=es_url)

    print(f'Waiting for Elasticsearch at {es_url}...')

    while True:
        try:
            if es_client.ping():
                print('Elasticsearch is ready!')
                break
        except Exception:
            pass
        time.sleep(2)
