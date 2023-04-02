from concurrent.futures import Future, _base

class AtomicInt:
    def __init__(self, value=0):
        self._future = Future()
        self._base = _base.FuturesSemaphore(1)
        self._value = value

    def get(self):
        return self._value

    def increment(self):
        with self._base:
            self._value += 1
            self._future.set_result(self._value)

    def decrement(self):
        with self._base:
            self._value -= 1
            self._future.set_result(self._value)

    def wait(self):
        self._future.result()