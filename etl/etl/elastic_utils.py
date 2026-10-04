import logging
from typing import Any, Dict, List, Set, Tuple

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, ConnectionTimeout
from elasticsearch.helpers import bulk

from utils import backoff

etl_logger = logging.getLogger('etl')


class ElasticBase:
    def __init__(self, es_url: str, index_name: str, index_config: dict):
        self.es = Elasticsearch(es_url)
        if not self.es.ping():
            raise ConnectionError(
                'Elasticsearch недоступен'
                )
        self.index_name = index_name
        self.index_config = index_config
        etl_logger.info('ElasticBase успешно инициализирован.')

    @backoff(exceptions=(ConnectionError, ConnectionTimeout))
    def add_index(self):
        if self.es.indices.exists(index=self.index_name):
            etl_logger.info(
                f'Индекс "{self.index_name}" существует. Пропускаем создание.'
                )
        else:
            print(f'Создаем индекс "{self.index_name}"...')
            self.es.indices.create(
                index=self.index_name,
                settings=self.index_config['settings'],
                mappings=self.index_config['mappings']
            )
            etl_logger.info(f'Индекс "{self.index_name}" успешно создан!')

    def gendata(self, documents):
        for movie in documents:
            yield {
                '_index': self.index_name,
                '_id': movie['id'],
                '_source': movie
            }

    @backoff(exceptions=(ConnectionError, ConnectionTimeout))
    def bulk_load(self, documents: List[Dict[str, Any]]) -> Tuple[int, int]:
        if not documents:
            return 0, 0
        success_count, errors = bulk(self.es, self.gendata(documents), raise_on_error=False)
        er_count = len(errors)
        if errors:
            etl_logger.error(f'Ошибок при первичной загрузке: {len(errors)}')
            failed_ids = self._extract_failed_ids(errors)
            sec_succes, sec_error = self.second_bulk(documents, failed_ids)
            success_count += sec_succes
            er_count += sec_error
        etl_logger.info(f'Успешно загружено: {success_count} документов')
        return success_count, len(errors)

    def second_bulk(self, documents: List[Dict[str, Any]], errors_ids: List[str]):
        documents_dict = {movie["id"]: movie for movie in documents}
        error_docs = [
            documents_dict[doc_id] for doc_id in errors_ids if doc_id in documents_dict
            ]
        if error_docs:
            retry_success, retry_errors = bulk(
                self.es,
                self.gendata(error_docs),
                raise_on_error=False,
            )
            if retry_errors:
                bad_ids = self._extract_failed_ids(retry_errors)
                etl_logger.error(
                    f'Повторная ошибка загрузки: документов. Ids: {bad_ids}'
                    )
            return retry_success, len(retry_errors)
        return 0, 0

    def _extract_failed_ids(self, errors: List[Dict]) -> Set[str]:
        error_ids = set()
        for err in errors:
            for op_type, op_result in err.items():
                doc_id = op_result.get('_id', 'unknown')
                error_ids.add(doc_id)
        return error_ids
