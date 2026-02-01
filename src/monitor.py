
import asyncio
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TokenAccountOpts
from solders.pubkey import Pubkey
from src.config import config
from src.notifier import BaseNotifier
from utils.logger import setup_logger

logger = setup_logger("Monitor")

# Standard SPL Token Program ID
TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")

class WalletMonitor:
    def __init__(self, notifier: BaseNotifier):
        self.notifier = notifier
        self.client = AsyncClient(config.RPC_URL)
        self.target_address = Pubkey.from_string(config.TARGET_WALLET)
        self.previous_sol_balance = None
        self.previous_token_balances = {} # Dict[MintAddress, Amount]
        self.is_running = False

    async def get_sol_balance(self) -> float:
        """Fetch the current SOL balance."""
        try:
            resp = await self.client.get_balance(self.target_address)
            return resp.value / 1_000_000_000
        except Exception as e:
            logger.error(f"Error fetching SOL balance: {e}")
            return None

    async def get_token_balances(self) -> dict:
        """Fetch all SPL token balances. Returns dict: {mint: ui_amount}"""
        try:
            # We use jsonParsed encoding to get readable data directly
            opts = TokenAccountOpts(program_id=TOKEN_PROGRAM_ID, encoding="jsonParsed")
            resp = await self.client.get_token_accounts_by_owner(self.target_address, opts)
            
            balances = {}
            for item in resp.value:
                # Parse the complex structure
                # item.account.data.parsed['info']['mint']
                # item.account.data.parsed['info']['tokenAmount']['uiAmount']
                try:
                    data = item.account.data.parsed['info']
                    mint = data['mint']
                    amount = data['tokenAmount']['uiAmount']
                    # Handle case where uiAmount might be None
                    if amount is None: amount = 0.0
                    balances[mint] = amount
                except KeyError:
                    continue
                    
            return balances
        except Exception as e:
            logger.error(f"Error fetching Token balances: {e}")
            return {}

    async def start(self):
        """Start the monitoring loop."""
        self.is_running = True
        logger.info("Starting polling loop...")
        
        # Initial check SOL
        current_sol = await self.get_sol_balance()
        if current_sol is not None:
             self.previous_sol_balance = current_sol
             logger.info(f"Initial SOL Balance: {self.previous_sol_balance} SOL")
             
        # Initial check Tokens
        current_tokens = await self.get_token_balances()
        self.previous_token_balances = current_tokens
        if current_tokens:
            logger.info(f"Tracking {len(current_tokens)} tokens.")
            for mint, amt in current_tokens.items():
                logger.debug(f"Token {mint[:8]}...: {amt}")
        
        while self.is_running:
            await asyncio.sleep(config.POLL_INTERVAL)
            
            # Check SOL
            new_sol = await self.get_sol_balance()
            if new_sol is not None:
                if self.previous_sol_balance is not None and new_sol != self.previous_sol_balance:
                    await self.handle_sol_change(new_sol)
                self.previous_sol_balance = new_sol
            
            # Check Tokens
            new_tokens = await self.get_token_balances()
            await self.check_token_changes(new_tokens)
            self.previous_token_balances = new_tokens

    async def handle_sol_change(self, new_balance: float):
        change = new_balance - self.previous_sol_balance
        direction = "RECEIVED" if change > 0 else "SENT"
        
        message = (
            f"Asset: SOL ☀️\n"
            f"Old Balance: {self.previous_sol_balance} SOL\n"
            f"New Balance: {new_balance} SOL\n"
            f"Change: {change:+.4f} SOL"
        )
        await self.notifier.send_alert(f"SOL Update: {direction}", message)

    async def check_token_changes(self, new_tokens: dict):
        # Check for modified or new tokens
        for mint, new_amt in new_tokens.items():
            old_amt = self.previous_token_balances.get(mint, 0.0)
            if new_amt != old_amt:
                await self.handle_token_change(mint, old_amt, new_amt)
        
        # Check for completely removed tokens (if balance becomes 0 it usually stays in dict as 0, strictly removed accounts are rare but possible)
        # For simplicity we just check modifies/adds

    async def handle_token_change(self, mint: str, old_amt: float, new_amt: float):
        change = new_amt - old_amt
        direction = "RECEIVED" if change > 0 else "SENT"
        # Shorten mint for display
        short_mint = f"{mint[:4]}...{mint[-4:]}"
        
        message = (
            f"Asset: Token ({short_mint}) 🪙\n"
            f"Old Balance: {old_amt}\n"
            f"New Balance: {new_amt}\n"
            f"Change: {change:+.4f}"
        )
        await self.notifier.send_alert(f"Token Update: {direction}", message)

    async def stop(self):
        logger.info("Stopping monitor...")
        self.is_running = False
        await self.client.close()
