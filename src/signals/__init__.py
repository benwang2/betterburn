import threading
import time
import weakref
from typing import Any, Callable, Dict, List


class ConnectionTimeoutManager:
    """
    A centralized manager to handle connection timeouts across all signals.
    Uses a singleton pattern to ensure a single cleanup thread for all connections.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Weak dictionary to track active connections
        self._connections: Dict[int, Connection] = {}
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._stop_event = threading.Event()
        self._cleanup_thread.start()

    def register_connection(self, connection: "Connection") -> None:
        """
        Register a connection for timeout tracking.

        Args:
            connection: Connection to be tracked
        """
        # Use id as a weak reference key
        self._connections[id(connection)] = weakref.ref(connection)

    def _cleanup_loop(self):
        """
        Continuous loop to check and clean up timed-out connections.
        Runs in a separate daemon thread.
        """
        while not self._stop_event.is_set():
            current_time = time.time()

            # Create a copy of keys to safely iterate
            connection_ids = list(self._connections.keys())

            for conn_id in connection_ids:
                # Retrieve the weak reference
                conn_ref = self._connections.get(conn_id)
                if not conn_ref:
                    # Reference was already garbage collected
                    self._connections.pop(conn_id, None)
                    continue

                # Attempt to get the actual connection
                connection = conn_ref()

                # If connection is gone, remove from tracking
                if not connection:
                    self._connections.pop(conn_id, None)
                    continue

                # Check if connection has timed out
                if current_time - connection._connection_time >= connection._timeout:
                    print(f"Timeout detected for connection {conn_id}")
                    connection.disconnect()
                    # Remove from tracking
                    self._connections.pop(conn_id, None)

            # Sleep to prevent constant checking
            time.sleep(1)

    def stop(self):
        """
        Stop the cleanup thread.
        """
        self._stop_event.set()
        self._cleanup_thread.join()


class Connection:
    def __init__(self, signal: "Signal", listener: Callable, timeout: float = 300):
        """
        Create a connection with an automatic timeout.

        Args:
            signal: The Signal this connection belongs to
            listener: The callback function to be managed
            timeout: Timeout in seconds (default 5 minutes)
        """
        self._signal = signal
        self._listener = listener
        self._is_connected = True
        self._connection_time = time.time()
        self._timeout = timeout

        # Register with the centralized timeout manager
        # ConnectionTimeoutManager().register_connection(self)

    def disconnect(self) -> None:
        """
        Disconnects the listener from the signal.
        """
        if not self._is_connected:
            return

        # Remove from signal's listeners
        if self._listener in self._signal.listeners:
            self._signal.listeners.remove(self._listener)

        if self._listener in self._signal.once_listeners:
            self._signal.once_listeners.remove(self._listener)

        self._is_connected = False
        print(f"Connection disconnected after {time.time() - self._connection_time:.2f} seconds")

    def is_connected(self) -> bool:
        """
        Check if the connection is still active.

        Returns:
            bool: True if the connection is still active, False otherwise
        """
        return self._is_connected


class Signal:
    def __init__(self):
        """
        Create a new Signal with empty listener lists.
        """
        self.listeners: List[Callable] = []
        self.once_listeners: List[Callable] = []

    async def emit(self, *args: Any, **kwargs: Any) -> None:
        """
        Emit the signal, calling all connected listeners.
        """
        # Create copies to allow modifications during iteration
        current_listeners = self.listeners.copy()
        current_once_listeners = self.once_listeners.copy()

        # Call regular listeners
        for f in current_listeners:
            await f(*args, **kwargs)

        # Call once listeners
        for f in current_once_listeners:
            f(*args, **kwargs)

        # Clear once listeners
        self.once_listeners.clear()

    def connect(self, f: Callable, timeout: float = 300) -> Connection:
        """
        Connect a listener to the signal with an optional timeout.

        Args:
            f: The listener function to connect
            timeout: Timeout in seconds (default 5 minutes)

        Returns:
            Connection: A connection object that can be used to disconnect
        """
        self.listeners.append(f)
        return Connection(self, f, timeout)


# Global signal
onUserLinked = Signal()
onUserUnlinked = Signal()


def create_timed_handler():
    """
    Create a handler that can be tracked by the centralized timeout manager.

    Returns:
        A connection handler function
    """

    def handler(connection: Connection, user: str):
        # Print when the handler is called
        print(f"Handling user: {user} at {time.ctime()}")

    # Create a wrapper function that takes the connection as its first argument
    def wrapper(user: str):
        # Create the connection with default 5-minute timeout
        connection = onUserLinked.connect(lambda u: handler(connection, u))

        # Immediately call the handler with the connection
        handler(connection, user)

    return wrapper
