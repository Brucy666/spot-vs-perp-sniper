import time
from collections import deque

class MultiTFMemory:
    def __init__(self):
        self.windows = {
            "1m":   {"max_age": 60,             "memory": deque()},
            "3m":   {"max_age": 3 * 60,         "memory": deque()},
            "5m":   {"max_age": 5 * 60,         "memory": deque()},
            "15m":  {"max_age": 15 * 60,        "memory": deque()},
            "30m":  {"max_age": 30 * 60,        "memory": deque()},
            "1h":   {"max_age": 60 * 60,        "memory": deque()},
            "4h":   {"max_age": 4 * 60 * 60,     "memory": deque()},
            "8h":   {"max_age": 8 * 60 * 60,     "memory": deque()},
            "12h":  {"max_age": 12 * 60 * 60,    "memory": deque()},
            "1d":   {"max_age": 24 * 60 * 60,    "memory": deque()}
        }

    def update(self, cb_cvd, bin_spot, bin_perp):
        now = time.time()
        datapoint = (now, cb_cvd, bin_spot, bin_perp)

        for tf in self.windows:
            self.windows[tf]["memory"].append(datapoint)
            self._cleanup_old(tf, now)

    def _cleanup_old(self, tf, now):
        memory = self.windows[tf]["memory"]
        max_age = self.windows[tf]["max_age"]
        while memory and now - memory[0][0] > max_age:
            memory.popleft()

    def get_all_deltas(self):
        deltas = {}
        for tf in self.windows:
            deltas[tf] = self._compute_delta(self.windows[tf]["memory"])
        return deltas

    def _compute_delta(self, memory):
        if len(memory) < 2:
            return {"cb_cvd": 0, "bin_spot": 0, "bin_perp": 0}

        start = memory[0]
        end = memory[-1]

        def percent_change(start_val, end_val):
            return round(((end_val - start_val) / abs(start_val)) * 100, 2) if start_val != 0 else 0

        return {
            "cb_cvd":   percent_change(start[1], end[1]),
            "bin_spot": percent_change(start[2], end[2]),
            "bin_perp": percent_change(start[3], end[3])
        }
