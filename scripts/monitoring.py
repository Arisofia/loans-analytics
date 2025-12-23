import logging
import time
import threading
import psutil
import os

logger = logging.getLogger("monitoring")

MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", 60))  # seconds


def log_resource_usage():
    while True:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        logger.info({
            "event": "resource_usage",
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "memory_used_mb": mem.used // 1024 // 1024,
            "memory_total_mb": mem.total // 1024 // 1024,
        })
        time.sleep(MONITOR_INTERVAL)

def start_monitoring():
    t = threading.Thread(target=log_resource_usage, daemon=True)
    t.start()

if __name__ == "__main__":
    start_monitoring()
    print("Advanced monitoring started. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("Monitoring stopped.")
