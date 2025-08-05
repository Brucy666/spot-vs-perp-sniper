# utils/multi_tf_memory.py

import time
from collections import deque

class MultiTFMemory:
    def __init__(self):
        self.timeframes = {
            "5m": 5 * 60,
            "15m": 15 * 60,
            "1h": 60 * 60,
            "4h": 4 * 60 * 60  # Optional: can remove if not needed
        }
        self.memory = {
            tf: deque() for tf in self.timeframes
        }

    def update(self, cb_cvd, bin_spot, bin_perp):
        now = time.time()
        snapshot = (now, cb_cvd, bin_spot, bin_perp)

        for tf in self.timeframes:
            self.memory[tf].append(snapshot)
            self._prune_old(tf, now)

    def _prune_old(self, tf, now):
        max_age = self.timeframes[tf]
        tf_memory = self.memory[tf]
        while tf_memory and (now - tf_memory[0][0]) > max_age:
            tf_memory.popleft()

    def get_all_deltas(self):
        return {
            tf: self._compute_deltas(self.memory[tf])
            for tf in self.memory
        }

    def _compute_deltas(self, data):
        if len(data) < 2:
            return {
                "cb_cvd": 0,
                "bin_spot": 0,
                "bin_perp": 0
            }

        _, cb_start, spot_start, perp_start = data[0]
        _, cb_end, spot_end, perp_end = data[-1]

        def pct_change(start, end):
            try:
                return round(((end - start) / abs(start)) * 100, 2) if start != 0 else 0
            except:
                return 0

        return {
            "cb_cvd": pct_change(cb_start, cb_end),
            "bin_spot": pct_change(spot_start, spot_end),
            "bin_perp": pct_change(perp_start, perp_end)
        }
