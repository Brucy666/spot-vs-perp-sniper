# utils/multi_tf_memory.py (shared by sniper, swing, reversal bots)

import time
from collections import deque

class MultiTFMemory:
    def __init__(self):
        self.windows = {
            "1m":   {"max_age": 60,         "memory": deque()},
            "3m":   {"max_age": 3 * 60,     "memory": deque()},
            "5m":   {"max_age": 5 * 60,     "memory": deque()},
            "15m":  {"max_age": 15 * 60,    "memory": deque()},
            "1h":   {"max_age": 60 * 60,    "memory": deque()},
            "4h":   {"max_age": 4 * 60 * 60, "memory": deque()}
        }

    def update(self, cb_cvd, bin_spot, bin_perp):
        now = time.time()
        point = (now, cb_cvd, bin_spot, bin_perp)

        for tf in self.windows:
            self.windows[tf]["memory"].append(point)
            self._cleanup(tf, now)

    def _cleanup(self, tf, now):
        max_age = self.windows[tf]["max_age"]
        memory = self.windows[tf]["memory"]
        while memory and now - memory[0][0] > max_age:
            memory.popleft()

    def get_all_deltas(self):
        return {
            tf: self._calculate_deltas(self.windows[tf]["memory"])
            for tf in self.windows
        }

    def _calculate_deltas(self, memory):
        if len(memory) < 2:
            return {"cb_cvd": 0, "bin_spot": 0, "bin_perp": 0}

        _, cb_start, spot_start, perp_start = memory[0]
        _, cb_end, spot_end, perp_end = memory[-1]

        def pct(a, b):
            return round(((b - a) / abs(a)) * 100, 2) if a != 0 else 0

        return {
            "cb_cvd": pct(cb_start, cb_end),
            "bin_spot": pct(spot_start, spot_end),
            "bin_perp": pct(perp_start, perp_end)
        }
