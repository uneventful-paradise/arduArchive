from abc import ABC, abstractmethod

class BaseClient(ABC):
    @abstractmethod
    def initiate_connection(self) -> None:
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