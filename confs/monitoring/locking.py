from logging import getLogger
from os import (
    close,
    O_CREAT,
    O_EXCL,
    O_RDWR,
    O_TRUNC,
    unlink,
)
from os import open as osopen
from threading import Lock
from time import (
    sleep,
    time,
)

_logger = None


def logger():
    global _logger
    _logger = _logger or getLogger(__name__)
    return _logger


class LockTimeout(TimeoutError):
    """
    Raised when the lock could not be acquired in *timeout* seconds.
    """

    def __init__(self, lock_file):
        self.lock_file = lock_file

    def __str__(self):
        return f"The file lock '{self.lock_file}' could not be acquired."


class FileLock(object):
    """
    Implements a file lock class.
    Extracted from https://raw.githubusercontent.com/benediktschmitt/py-filelock/master/filelock.py
    And https://github.com/dmfrey/FileLock/blob/master/filelock/filelock.py
    """

    def __init__(self, lock_file, timeout=-1):
        self._lock_file = lock_file
        self._lock_file_fd = None
        self.timeout = timeout
        self._thread_lock = Lock()
        self._lock_counter = 0

    @property
    def lock_file(self):
        return self._lock_file

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = float(value)

    def _acquire(self):
        open_mode = O_CREAT | O_EXCL | O_RDWR | O_TRUNC
        try:
            self._lock_file_fd = osopen(self._lock_file, open_mode)
        except (IOError, OSError):
            self._lock_file_fd = None
            logger().debug(f"Cannot acquire lock {self._lock_file}")

    def _release(self):
        fd = self._lock_file_fd
        unlink(self._lock_file)
        close(fd)
        self._lock_file_fd = None

    @property
    def is_locked(self):
        return self._lock_file_fd is not None

    def acquire(self, timeout=None, poll_intervall=0.05):
        if timeout is None:
            timeout = self.timeout
        with self._thread_lock:
            self._lock_counter += 1
        lock_id = id(self)
        lock_filename = self._lock_file
        start_time = time()
        try:
            while True:
                with self._thread_lock:
                    if not self.is_locked:
                        logger().debug(f"Attempting to acquire lock {lock_id} on {lock_filename}")
                        self._acquire()
                if self.is_locked:
                    logger().info(f"Lock {lock_id} acquired on {lock_filename}")
                    break
                elif timeout >= 0 and time() - start_time > timeout:
                    logger().debug(f"Timeout on acquiring lock {lock_id} on {lock_filename}")
                    raise LockTimeout(self._lock_file)
                else:
                    logger().debug(f"Lock {lock_id} not acquired on {lock_filename}, waiting {poll_intervall} seconds ...")
                    sleep(poll_intervall)
        except Exception:
            # Something did go wrong, so decrement the counter.
            with self._thread_lock:
                self._lock_counter = max(0, self._lock_counter - 1)
            raise

    def release(self, force=False):
        with self._thread_lock:
            if self.is_locked:
                self._lock_counter -= 1
                if self._lock_counter == 0 or force:
                    lock_id = id(self)
                    lock_filename = self._lock_file
                    logger().debug(f"Attempting to release lock {lock_id} on {lock_filename}")
                    self._release()
                    self._lock_counter = 0
                    logger().info(f"Lock {lock_id} released on {lock_filename}")

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()

    def __del__(self):
        self.release(force=True)
