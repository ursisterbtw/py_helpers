import json
import os
import requests
from typing import Dict, List, Optional
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
            "type": "function",
        },
        {"inputs": [], "name": "decimals", "outputs": [{"type": "uint8"}], "stateMutability": "view", "type": "function"},
        {
            "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
            "name": "approve",
            "outputs": [{"type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
    ],
    "UniswapV2Router": [
        {
            "inputs": [{"name": "amountIn", "type": "uint256"}, {"name": "path", "type": "address[]"}],
            "name": "getAmountsOut",
            "outputs": [{"type": "uint256[]"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"name": "amountOutMin", "type": "uint256"},
                {"name": "path", "type": "address[]"},
                {"name": "to", "type": "address"},
                {"name": "deadline", "type": "uint256"},
            ],
            "name": "swapExactETHForTokens",
            "outputs": [{"type": "uint256[]"}],
            "stateMutability": "payable",
            "type": "function",
        },
    ],
    "UniswapV2Factory": [
        {
            "inputs": [{"name": "tokenA", "type": "address"}, {"name": "tokenB", "type": "address"}],
            "name": "getPair",
            "outputs": [{"type": "address"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "token0", "type": "address"},
                {"indexed": True, "name": "token1", "type": "address"},
                {"indexed": False, "name": "pair", "type": "address"},
                {"indexed": False, "name": "", "type": "uint256"},
            ],
            "name": "PairCreated",
            "type": "event",
        },
    ],
}


def fetch_abi_from_etherscan(contract_address: str) -> Optional[List]:
    """Fetch full ABI from Etherscan."""
    if not ETHERSCAN_API_KEY:
        print("Warning: No Etherscan API key provided. Skipping fetch.")
        return None

    params = {"module": "contract", "action": "getabi", "address": contract_address, "apikey": ETHERSCAN_API_KEY}

    try:
        response = requests.get(ETHERSCAN_API, params=params)
        response.raise_for_status()
        data = response.json()

        if data["status"] == "1" and data["message"] == "OK":
            return json.loads(data["result"])
        else:
            print(f"Error fetching ABI: {data['message']}")
            return None
    except Exception as e:
        print(f"Error fetching ABI for {contract_address}: {str(e)}")
        return None


def save_abi(name: str, abi: List, directory: str = "abi") -> None:
    """Save ABI to a JSON file."""
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, f"{name}.json")

    with open(filepath, "w") as f:
        json.dump(abi, f, indent=2)
    print(f"Created {filepath}")


def main():
    # First, save our minimal ABIs
    for name, abi in MINIMAL_ABIS.items():
        save_abi(name, abi)

    # Then fetch and save full ABIs for known contracts
    if ETHERSCAN_API_KEY:
        print("\nFetching full ABIs from Etherscan...")
        for name, address in CONTRACTS.items():
            print(f"Fetching {name}...")
            abi = fetch_abi_from_etherscan(address)
            if abi:
                save_abi(f"{name}_full", abi)


if __name__ == "__main__":
    main()
