
import solana
from solana.rpc.api import Client
from solders.pubkey import Pubkey
import os
from dotenv import load_dotenv
import time

# Load env to get the same target wallet
load_dotenv()

TARGET_WALLET = os.getenv("TARGET_WALLET_ADDRESS")

def trigger_airdrop():
    if not TARGET_WALLET:
        print("Error: TARGET_WALLET_ADDRESS not set in .env")
        return

    print(f"Triggering event for: {TARGET_WALLET}")
    client = Client("https://api.devnet.solana.com")
    
    pubkey = Pubkey.from_string(TARGET_WALLET)
    
    print("Requesting 1 SOL airdrop...")
    try:
        resp = client.request_airdrop(pubkey, 500_000_000)
        print(f"Airdrop requested! Signature: {resp.value}")
        print("Now wait for Sentinel to pick it up...")
    except Exception as e:
        print(f"Airdrop failed: {e}")

if __name__ == "__main__":
    trigger_airdrop()
