"""Main worker process."""

import asyncio
import logging
import signal
from worker.config import settings
from worker.database import init_database
from worker.consumer import MetricConsumer

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
    
    # Create consumer
    consumer = MetricConsumer()
    
    # Handle shutdown
    loop = asyncio.get_event_loop()
    
    def handle_shutdown(sig):
        logger.info(f"Received signal {sig}, shutting down...")
        loop.create_task(consumer.stop())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: handle_shutdown(s))
    
    # Start consuming
    try:
        await consumer.start()
        await consumer.consume()
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
