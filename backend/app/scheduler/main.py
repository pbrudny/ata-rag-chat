import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SessionLocal
from app.pipeline.sync import run_daily_sync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _run_sync_job() -> None:
    db = SessionLocal()
    try:
        run = run_daily_sync(db)
        logger.info(
            "Daily sync finished: status=%s discovered=%d updated=%d failed=%d removed=%d",
            run.status,
            run.pages_discovered,
            run.pages_updated,
            run.pages_failed,
            run.pages_removed,
        )
    finally:
        db.close()


def main() -> None:
    scheduler = BackgroundScheduler()
    scheduler.add_job(_run_sync_job, "cron", hour=3, minute=0)
    scheduler.start()
    logger.info("Scheduler started; daily sync scheduled for 03:00")

    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()
