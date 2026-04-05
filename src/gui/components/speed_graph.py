"""Download speed graph component."""
import time
from collections import deque
from src.utils.logger import get_logger
logger = get_logger(__name__)

class SpeedGraph:
    def __init__(self, max_points=60):
        self.max_points = max_points
        self.data = deque(maxlen=max_points)
        self.start_time = None

    def start(self):
        self.start_time = time.time()
        self.data.clear()

    def add_point(self, speed_bps):
        elapsed = time.time() - self.start_time if self.start_time else 0
        self.data.append((elapsed, speed_bps))

    def get_data(self):
        return list(self.data)

    def get_average_speed(self):
        if not self.data: return 0
        return sum(s for _, s in self.data) / len(self.data)

    def get_peak_speed(self):
        if not self.data: return 0
        return max(s for _, s in self.data)

    def get_current_speed(self):
        if not self.data: return 0
        return self.data[-1][1]

    def format_speed(self, speed_bps):
        if speed_bps > 1_000_000_000: return f"{speed_bps/1_000_000_000:.2f} GB/s"
        if speed_bps > 1_000_000: return f"{speed_bps/1_000_000:.2f} MB/s"
        if speed_bps > 1_000: return f"{speed_bps/1_000:.2f} KB/s"
        return f"{speed_bps:.0f} B/s"
