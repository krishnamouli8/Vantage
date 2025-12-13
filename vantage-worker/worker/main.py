"""Main worker process."""

import asyncio
import logging
import signal
from worker.config import settings
from worker.database import init_database
from worker.consumer import MetricConsumer
from worker.periodic_tasks import PeriodicTasks

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


async def main():
    """Main worker loop."""
    logger.info("Starting Vantage Worker...")
    
    # Initialize database
    init_database()
    
    # Create consumer and periodic tasks
    consumer = MetricConsumer()
    periodic_tasks = PeriodicTasks()
    
    # Handle shutdown
    loop = asyncio.get_event_loop()
    
    def handle_shutdown(sig):
        logger.info(f"Received signal {sig}, shutting down...")
        loop.create_task(consumer.stop())
        loop.create_task(periodic_tasks.stop())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: handle_shutdown(s))
    
    # Start services
    try:
        await consumer.start()
        await periodic_tasks.start()
        await consumer.consume()
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
    finally:
        await periodic_tasks.stop()
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())

