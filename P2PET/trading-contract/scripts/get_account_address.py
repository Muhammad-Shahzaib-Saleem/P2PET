#!/usr/bin/env python3
import os, time
import json
from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from eth_account import Account
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Load config from .env
RPC_URL = os.getenv("LOCAL_RPC_URL")
ABI_PATH = os.getenv("ABI_PATH")
CONTRACT_ADDRESS_PATH = os.getenv("CONTRACT_ADDRESS_PATH")

# Read deployed contract address
with open(CONTRACT_ADDRESS_PATH, "r") as f:
    data = json.load(f)
    CONTRACT_ADDRESS = data["contract_address"]
    # CONTRACT_ADDRESS = f.read().strip()

# Connect to Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
private_key = PRIVATE_KEY


account = w3.eth.account.from_key(private_key)
sender_address = account.address

print("Account Address: ", sender_address)