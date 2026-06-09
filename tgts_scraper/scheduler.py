"""
Scheduler module for running scraper on a schedule
Can be used with APScheduler or system cron/Task Scheduler
"""

import logging
import sys
try:
    import schedule
    import time
except ImportError:
    schedule = None

logger = logging.getLogger(__name__)


class TenderScheduler:
    """Schedules scraper execution"""

    def __init__(self, job_func, run_time: str = "09:00"):
        """
        Initialize scheduler
        job_func: Function to schedule
        run_time: Time in HH:MM format
        """
        if not schedule:
            logger.warning("schedule library not installed. Install with: pip install schedule")
            return

        self.job_func = job_func
        self.run_time = run_time

    def schedule_daily(self):
        """Schedule daily job"""
        if not schedule:
            logger.error("Cannot schedule - schedule library not available")
            return False

        try:
            schedule.every().day.at(self.run_time).do(self.job_func)
            logger.info(f"Job scheduled daily at {self.run_time}")
            return True
        except Exception as e:
            logger.error(f"Error scheduling job: {e}")
            return False

    def start(self):
        """Start scheduler (blocking)"""
        if not schedule:
            logger.error("Cannot start scheduler - schedule library not available")
            return

        logger.info("Scheduler started - press Ctrl+C to stop")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped")
            sys.exit(0)

    @staticmethod
    def run_once_on_startup(job_func):
        """Run job immediately on startup"""
        try:
            logger.info("Running job on startup...")
            job_func()
        except Exception as e:
            logger.error(f"Error running startup job: {e}")


# Usage example:
# from scheduler import TenderScheduler
# from main import main
#
# if __name__ == "__main__":
#     scheduler = TenderScheduler(main, run_time="09:00")
#     scheduler.schedule_daily()
#     scheduler.start()
