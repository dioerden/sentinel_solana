
import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from src.config import config
from src.notifier import BaseNotifier
from utils.logger import setup_logger

logger = setup_logger("Monitor")

class WalletMonitor:
    def __init__(self, notifier: BaseNotifier):
        self.notifier = notifier
        self.client = AsyncClient(config.RPC_URL)
        self.target_address = Pubkey.from_string(config.TARGET_WALLET)
        self.previous_balance = None
        self.is_running = False

    async def get_balance(self) -> float:
        """Fetch the current balance in SOL."""
        try:
            resp = await self.client.get_balance(self.target_address)
            # Handle different versions of solana-py response structure if needed
            # Assuming resp.value is the lamports
            return resp.value / 1_000_000_000
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return None

    async def start(self):
        """Start the monitoring loop."""
        self.is_running = True
        logger.info("Starting polling loop...")
        
        # Initial check
        current_balance = await self.get_balance()
        if current_balance is not None:
             self.previous_balance = current_balance
             logger.info(f"Initial Balance: {self.previous_balance} SOL")
        
        while self.is_running:
            await asyncio.sleep(config.POLL_INTERVAL)
            
            new_balance = await self.get_balance()
            
            if new_balance is None:
                continue

            if self.previous_balance is not None and new_balance != self.previous_balance:
                await self.handle_balance_change(new_balance)
            
            self.previous_balance = new_balance

    async def handle_balance_change(self, new_balance: float):
        change = new_balance - self.previous_balance
        direction = "RECEIVED" if change > 0 else "SENT"
        
        message = (
            f"Address: {self.target_address}\n"
            f"Old Balance: {self.previous_balance} SOL\n"
            f"New Balance: {new_balance} SOL\n"
            f"Change: {change:+.4f} SOL"
        )
        
        await self.notifier.send_alert(f"Balance Update: {direction}", message)

    async def stop(self):
        logger.info("Stopping monitor...")
        self.is_running = False
        await self.client.close()
