import threading, time
from datetime import datetime, timedelta

class AttackScheduler:
    def __init__(self, log_func=None):
        self.log = log_func or print
        self.jobs = []

    def schedule_at(self, time_str, target, method, threads, attack_callback):
        """
        time_str: HH:MM
        attack_callback: функция, которая будет вызвана (без аргументов) в нужное время
        """
        def waiter():
            now = datetime.now()
            target_time = datetime.strptime(time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
            if target_time < now:
                target_time += timedelta(days=1)
            delay = (target_time - now).total_seconds()
            self.log(f"[Расписание] Атака запланирована на {target_time.strftime('%Y-%m-%d %H:%M')} (через {int(delay)} сек)\n")
            time.sleep(delay)
            attack_callback()
            self.log(f"[Расписание] Атака запущена по расписанию\n")
        t = threading.Thread(target=waiter, daemon=True)
        t.start()
        self.jobs.append(t)