
import os
from dotenv import load_dotenv
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from utils.logger import setup_logger

logger = setup_logger("Config")

class Config:
    def __init__(self):
        load_dotenv()
        
        self.RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
        self.TARGET_WALLET = os.getenv("TARGET_WALLET_ADDRESS")
        self.POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))
        
        self.validate()

    def validate(self):
        """Validates critical configuration."""
        if not self.TARGET_WALLET:
            logger.error("TARGET_WALLET_ADDRESS is missing in .env")
            raise ValueError("TARGET_WALLET_ADDRESS must be set in .env")
        
        try:
            # Validate if it's a correct Pubkey format
            Pubkey.from_string(self.TARGET_WALLET)
        except Exception:
            logger.error(f"Invalid Solana Address: {self.TARGET_WALLET}")
            raise ValueError("Invalid Solana Address provided.")
            
        logger.info("Configuration loaded successfully.")
        logger.info(f"Tracking Wallet: {self.TARGET_WALLET}")
        logger.info(f"RPC URL: {self.RPC_URL}")

config = Config()
