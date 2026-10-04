import abc
import json
from typing import Any, Dict


class BaseStorage(abc.ABC):
    """Абстрактное хранилище состояния.

    Позволяет сохранять и получать состояние.
    Способ хранения состояния может варьироваться в зависимости
    от итоговой реализации. Например, можно хранить информацию
    в базе данных или в распределённом файловом хранилище.
    """

    @abc.abstractmethod
    def save_state(self, state: Dict[str, Any]) -> None:
        """Сохранить состояние в хранилище."""

    @abc.abstractmethod
    def retrieve_state(self) -> Dict[str, Any]:
        """Получить состояние из хранилища."""


class JsonFileStorage(BaseStorage):
    """Реализация хранилища, использующего локальный файл.

    Формат хранения: JSON
    """

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def save_state(self, state: Dict[str, Any]) -> None:
        """Сохранить состояние в хранилище."""
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(state, file, ensure_ascii=False, indent=4)

    def retrieve_state(self) -> Dict[str, Any]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}


class State:
    """Класс для работы с состояниями."""

    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage
        self._state = self.storage.retrieve_state()

    def set_state(self, key: str, value: Any) -> None:
        """Установить состояние для определённого ключа."""
        self._state[key] = value
        self.storage.save_state(self._state)

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу."""
        return self._state.get(key)

    def get_state_or_late(self, key: str) -> Any:
        """Получить состояние даты по ключу или вернуть очень старую."""
        return self._state.get(key) or '1900-01-01T01:01:01.000001'

    def get_uid_state_or_late(self, key: str) -> Any:
        """Получить состояние uid по ключу или вернуть начальный."""
        return self._state.get(key) or '00000000-0000-0000-0000-000000000000'

    def update_state(self, updates: Dict[str, Any]) -> None:
        self._state.update(updates)
        self.storage.save_state(self._state)

    def get_all_state(self):
        return {
            'film_work_modified': self.get_state_or_late('film_work_modified'),
            'film_work_id': self.get_uid_state_or_late('film_work_id'),
            'person_modified': self.get_state_or_late('person_modified'),
            'person_id': self.get_uid_state_or_late('person_id'),
            'genre_modified': self.get_state_or_late('genre_modified'),
            'genre_id': self.get_uid_state_or_late('genre_id'),
            'person_film_work_modified': self.get_state_or_late('person_film_work_modified'),
            'person_film_work_id': self.get_uid_state_or_late('person_film_work_id'),
            'genre_film_work_modified': self.get_state_or_late('genre_film_work_modified'),
            'genre_film_work_id': self.get_uid_state_or_late('genre_film_work_id'),
        }

