import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Constants
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
ETHERSCAN_API = "https://api.etherscan.io/api"

# Common contract addresses
CONTRACTS = {
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "UniswapV2Router02": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "UniswapV2Factory": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
    "SushiSwapRouter": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
}

# Minimal ABIs for common contracts
MINIMAL_ABIS = {
    "ERC20": [
        {
            "inputs": [{"name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "decimals",
            "outputs": [{"type": "uint8"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
            "name": "approve",
            "outputs": [{"type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ],
    "UniswapV2Router": [
        {
            "inputs": [
                {"name": "amountIn", "type": "uint256"},
                {"name": "path", "type": "address[]"}
            ],
            "name": "getAmountsOut",
            "outputs": [{"type": "uint256[]"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {"name": "amountOutMin", "type": "uint256"},
                {"name": "path", "type": "address[]"},
                {"name": "to", "type": "address"},
                {"name": "deadline", "type": "uint256"}
            ],
            "name": "swapExactETHForTokens",
            "outputs": [{"type": "uint256[]"}],
            "stateMutability": "payable",
            "type": "function"
        }
    ],
    "UniswapV2Factory": [
        {
            "inputs": [
                {"name": "tokenA", "type": "address"},
                {"name": "tokenB", "type": "address"}
            ],
            "name": "getPair",
            "outputs": [{"type": "address"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "token0", "type": "address"},
                {"indexed": True, "name": "token1", "type": "address"},
                {"indexed": False, "name": "pair", "type": "address"},
                {"indexed": False, "name": "", "type": "uint256"}
            ],
            "name": "PairCreated",
            "type": "event"
        }
    ]
}


class ABIGenerator:
    def __init__(self):
        self.setup_constants()
        self.setup_directories()

    def setup_constants(self):
        """Initialize constants and configurations"""
        self.ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
        self.ETHERSCAN_API = "https://api.etherscan.io/api"
        self.OUTPUT_DIR = Path("abi")
        self.BACKUP_DIR = self.OUTPUT_DIR / "backups"

        # Network configurations
        self.NETWORKS = {
            "mainnet": "https://api.etherscan.io/api",
            "goerli": "https://api-goerli.etherscan.io/api",
            "sepolia": "https://api-sepolia.etherscan.io/api",
        }

        # Common contract addresses
        self.CONTRACTS = {
            "DEX": {
                "UniswapV2Router02": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
                "UniswapV2Factory": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
                "SushiSwapRouter": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
            },
            "Tokens": {
                "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            }
        }

    def setup_directories(self):
        """Create necessary directories"""
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        self.BACKUP_DIR.mkdir(exist_ok=True)

    def backup_existing_abis(self):
        """Backup existing ABI files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.BACKUP_DIR / timestamp

        if list(self.OUTPUT_DIR.glob("*.json")):
            backup_dir.mkdir(exist_ok=True)
            for file in self.OUTPUT_DIR.glob("*.json"):
                if file.parent != self.BACKUP_DIR:
                    backup_path = backup_dir / file.name
                    backup_path.write_text(file.read_text())
            print(f"✅ Backed up existing ABIs to {backup_dir}")

    def fetch_abi_from_etherscan(self, contract_address: str, network: str = "mainnet") -> Optional[List]:
        """Fetch full ABI from Etherscan with rate limiting and retries"""
        if not self.ETHERSCAN_API_KEY:
            print("⚠️  No Etherscan API key provided. Skipping fetch.")
            return None

        api_url = self.NETWORKS.get(network, self.NETWORKS["mainnet"])
        params = {
            "module": "contract",
            "action": "getabi",
            "address": contract_address,
            "apikey": self.ETHERSCAN_API_KEY
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(api_url, params=params)
                response.raise_for_status()
                data = response.json()

                if data["status"] == "1" and data["message"] == "OK":
                    return json.loads(data["result"])
                else:
                    print(f"⚠️  Error fetching ABI: {data['message']}")
                    return None
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(
                        f"⚠️  Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(
                        f"❌ Error fetching ABI for {contract_address}: {str(e)}")
                    return None

    def save_abi(self, name: str, abi: List) -> None:
        """Save ABI to a JSON file with pretty formatting"""
        filepath = self.OUTPUT_DIR / f"{name}.json"

        with open(filepath, "w") as f:
            json.dump(abi, f, indent=2)
        print(f"✅ Created {filepath}")

    def generate_abis(self, fetch_full: bool = True, network: str = "mainnet"):
        """Main ABI generation process"""
        print("\n🚀 Starting ABI generation process...")

        # Backup existing ABIs
        self.backup_existing_abis()

        # Save minimal ABIs
        print("\n📝 Generating minimal ABIs...")
        for name, abi in MINIMAL_ABIS.items():
            self.save_abi(name, abi)

        # Fetch full ABIs if requested
        if fetch_full and self.ETHERSCAN_API_KEY:
            print("\n🌐 Fetching full ABIs from Etherscan...")
            for category, contracts in self.CONTRACTS.items():
                print(f"\n📂 Category: {category}")
                for name, address in contracts.items():
                    print(f"⏳ Fetching {name}...")
                    abi = self.fetch_abi_from_etherscan(address, network)
                    if abi:
                        self.save_abi(f"{name}_full", abi)
                    time.sleep(0.2)  # Rate limiting

        print("\n✨ ABI generation complete!")


def main():
    # Initialize generator
    generator = ABIGenerator()

    # Parse command line arguments (you could add argparse here)
    fetch_full = True
    network = "mainnet"

    # Generate ABIs
    generator.generate_abis(fetch_full=fetch_full, network=network)


if __name__ == "__main__":
    main()
