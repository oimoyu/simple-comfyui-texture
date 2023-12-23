import threading
from .utils import SingletonMeta, set_progress_msg


class AsyncTask(metaclass=SingletonMeta):
    FREE = "free"
    RUNNING = "running"
    DONE = "done"

    def __init__(self):
        self.task = None
        self._status = self.FREE
        self._task_thread = None
        self.stop_flag = False
        self.process_msg = ""
        self.progress = 0.0

    def run_task(self, func, *args, **kwargs):
        self.stop_flag = False
        if self._status == self.RUNNING:
            set_progress_msg("A thread is running")
            return

        def thread_target():
            try:
                func(*args, **kwargs)
            finally:
                self._status = self.FREE

        self._task_thread = threading.Thread(target=thread_target)
        self._task_thread.start()
        self._status = self.RUNNING

    @property
    def status(self):
        if self._task_thread is None or not self._task_thread.is_alive():
            return self.FREE

        return self.RUNNING


task = AsyncTask()
