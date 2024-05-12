import abc


class Limiter(abc.ABC):
    @abc.abstractmethod
    def is_too_long(self, result: str) -> bool:
        raise NotImplementedError
