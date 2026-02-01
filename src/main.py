
import asyncio
import sys
from utils.logger import setup_logger
from src.config import config
from src.monitor import WalletMonitor
from src.notifier import ConsoleNotifier

logger = setup_logger("Main")

async def main():
    logger.info("Initializing Sentinel...")
    
    # Initialize components
    notifier = ConsoleNotifier()
    monitor = WalletMonitor(notifier=notifier)
    
    logger.info(f"Sentinel is watching: {config.TARGET_WALLET}")
    logger.info("Press Ctrl+C to stop.")

    try:
        await monitor.start()
    except asyncio.CancelledError:
        logger.info("Sentinel stopped by user.")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
    finally:
        await monitor.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Allow graceful exit on Ctrl+C from terminal
        pass
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
