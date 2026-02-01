
from abc import ABC, abstractmethod
from utils.logger import setup_logger

logger = setup_logger("Notifier")

class BaseNotifier(ABC):
    """Abstract base class for all notifiers."""
    
    @abstractmethod
    async def send_alert(self, title: str, message: str):
        """Send a notification."""
        pass

class ConsoleNotifier(BaseNotifier):
    """Simple notifier that logs to the console."""
    
    async def send_alert(self, title: str, message: str):
        logger.info("="*30)
        logger.info(f"🔔 {title.upper()} 🔔")
        logger.info(f"{message}")
        logger.info("="*30)
