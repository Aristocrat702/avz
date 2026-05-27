import threading
import asyncio
from croniter import croniter
from datetime import datetime
from engine.attack import AsyncAttackEngine

class Scheduler:
    def __init__(self):
        self.tasks = []
        self.engine = AsyncAttackEngine()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def add_task(self, cron_expr, method, target, port, duration):
        self.tasks.append({
            "cron": cron_expr,
            "method": method,
            "target": target,
            "port": port,
            "duration": duration
        })

    def _loop(self):
        while True:
            now = datetime.now()
            for task in self.tasks:
                if croniter.match(task["cron"], now):
                    asyncio.run(self.engine.run_attack(
                        task["method"],
                        task["target"],
                        task["port"],
                        task["duration"]
                    ))
            threading.Event().wait(30)
