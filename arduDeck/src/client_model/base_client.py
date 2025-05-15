from abc import ABC, abstractmethod

class BaseClient(ABC):
    @property
    @abstractmethod
    def chunk_size(self) -> int:
        pass

    @abstractmethod
    def initiate_connection(self) -> None:
        pass

    @abstractmethod
    def check_connection(self) -> bool:
        pass

    @abstractmethod
    def read_all(self, req_len: int) -> bytes:
        pass

    @abstractmethod
    def write_all(self, data: bytes) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass