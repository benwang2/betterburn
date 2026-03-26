from __future__ import annotations

from typing import Any, Awaitable, Callable, List

from ..custom_logger import CustomLogger

logger = CustomLogger("signals")


AsyncListener = Callable[..., Awaitable[None]]


class Signal:
    """A small async signal/event emitter used for link/unlink hooks.

    Contract:
    - Listeners must be async callables
    - Exceptions are logged and don't stop other listeners
    """

    def __init__(self) -> None:
        self._listeners: List[AsyncListener] = []

    def connect(self, f: AsyncListener) -> None:
        self._listeners.append(f)

    def disconnect(self, f: AsyncListener) -> None:
        try:
            self._listeners.remove(f)
        except ValueError:
            return

    async def emit(self, *args: Any, **kwargs: Any) -> None:
        for f in list(self._listeners):
            try:
                await f(*args, **kwargs)
            except Exception as e:  # pragma: no cover
                logger.error("Signal listener raised", error=str(e), listener=getattr(f, "__name__", str(f)))


onUserLinked = Signal()
onUserUnlinked = Signal()
