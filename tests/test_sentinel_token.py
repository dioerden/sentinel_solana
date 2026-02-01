
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
from src.monitor import WalletMonitor
from src.notifier import BaseNotifier
from solders.pubkey import Pubkey

class MockNotifier(BaseNotifier):
    def __init__(self):
        self.alerts = []

    async def send_alert(self, title: str, message: str):
        self.alerts.append((title, message))

class TestSentinel(unittest.IsolatedAsyncioTestCase):
    
    @patch("src.monitor.AsyncClient")
    async def test_monitor_detects_token_change(self, mock_client_cls):
        # Setup Mocks
        mock_client = mock_client_cls.return_value
        
        # 1. Mock SOL Balance
        mock_sol_resp = MagicMock()
        mock_sol_resp.value = 1_000_000_000
        mock_client.get_balance = AsyncMock(return_value=mock_sol_resp)
        
        # 2. Mock Token Response Helper
        def create_token_resp(mint, amount):
            item = MagicMock()
            item.account.data.parsed = {
                'info': {
                    'mint': mint,
                    'tokenAmount': {'uiAmount': amount}
                }
            }
            resp = MagicMock()
            resp.value = [item]
            return resp

        resp_1 = create_token_resp("USDC_MINT_ADDRESS", 10.0)
        resp_2 = create_token_resp("USDC_MINT_ADDRESS", 25.0)
        
        # Force the side effect to be EXACTLY what we want
        mock_client.get_token_accounts_by_owner = AsyncMock(side_effect=[resp_1, resp_2, resp_2])
        
        # Initialize Monitor
        notifier = MockNotifier()
        monitor = WalletMonitor(notifier)
        monitor.target_address = Pubkey.from_string("11111111111111111111111111111111")
        monitor.client = mock_client
        
        # --- EXECUTION ---
        
        # 1. First Call: Should return 10.0
        print("DEBUG: Calling get_token_balances #1")
        val1 = await monitor.get_token_balances()
        monitor.previous_token_balances = val1
        print(f"DEBUG: Result #1: {val1}")
        
        # Check integrity of first call
        self.assertEqual(val1.get("USDC_MINT_ADDRESS"), 10.0, f"Expected 10.0, got {val1}")
        
        # 2. Second Call: Should return 25.0
        print("DEBUG: Calling get_token_balances #2")
        new_tokens = await monitor.get_token_balances()
        print(f"DEBUG: Result #2: {new_tokens}")
        
        # Check integrity of second call
        self.assertEqual(new_tokens.get("USDC_MINT_ADDRESS"), 25.0, f"Expected 25.0, got {new_tokens}")
        
        # 3. Simulate Change Detection
        await monitor.check_token_changes(new_tokens)
        
        # Verify Alert
        self.assertEqual(len(notifier.alerts), 1)
        title, msg = notifier.alerts[0]
        
        self.assertEqual(title, "Token Update: RECEIVED")
        self.assertIn("USDC...", msg)
        self.assertIn("Old Balance: 10.0", msg)
        self.assertIn("New Balance: 25.0", msg)
        
        print("\nTest Passed: Monitor correctly detected SPL Token increase!")

if __name__ == "__main__":
    unittest.main()
