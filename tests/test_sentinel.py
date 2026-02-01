
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
    async def test_monitor_detects_balance_change(self, mock_client_cls):
        # Setup Mocks
        mock_client = mock_client_cls.return_value
        # Mock responses: First call 1.0 SOL, Second call 1.5 SOL
        # get_balance returns a response object with a .value attribute (lamports)
        
        mock_resp_1 = MagicMock()
        mock_resp_1.value = 1_000_000_000 # 1 SOL
        
        mock_resp_2 = MagicMock()
        mock_resp_2.value = 1_500_000_000 # 1.5 SOL
        
        mock_client.get_balance = AsyncMock(side_effect=[mock_resp_1, mock_resp_2, mock_resp_2])
        
        # Initialize Monitor
        notifier = MockNotifier()
        monitor = WalletMonitor(notifier)
        monitor.target_address = Pubkey.from_string("11111111111111111111111111111111") # Dummy
        
        # Overwrite start to only run a few loops then stop
        # Or better, test logic directly
        
        # 1. Initial State
        monitor.client = mock_client # Inject mock
        bal = await monitor.get_balance()
        monitor.previous_balance = bal
        
        self.assertEqual(monitor.previous_balance, 1.0)
        
        # 2. Simulate Polling Change
        new_bal = await monitor.get_balance() # Returns 1.5
        
        await monitor.handle_balance_change(new_bal)
        monitor.previous_balance = new_bal
        
        # Verify Alert
        self.assertEqual(len(notifier.alerts), 1)
        title, msg = notifier.alerts[0]
        self.assertEqual(title, "Balance Update: RECEIVED")
        self.assertIn("Old Balance: 1.0 SOL", msg)
        self.assertIn("New Balance: 1.5 SOL", msg)
        self.assertIn("Change: +0.5000 SOL", msg)
        
        print("\nTest Passed: Monitor correctly detected balance increase!")

if __name__ == "__main__":
    unittest.main()
