#!/usr/bin/env python3

import json
import os
from web3 import Web3
from matching import Offer, greedy_double_auction
from eth_utils import keccak


SCALING_FACTOR = 100  # Must match scaling in contract submission

def fetch_all_participants(contract):
    """Fetch participant data from the smart contract."""
    offers = []
    for i in range(10):  # Make sure this matches number of participants in contract
        try:
            addr, role, energy, price = contract.functions.participantsList(i).call()

            if role == 0:  # Role.N_A
                continue

            role_str = "buyer" if role == 1 else "seller"

            # Unscale energy and price
            energy = energy / SCALING_FACTOR
            price = price / SCALING_FACTOR

            offers.append(Offer(addr, role_str, energy, price))
        except Exception as e:
            print(f"Error fetching slot {i}: {e}")
    return offers


def run_matching_and_get_hash(contract):
    """Runs the double auction matching and returns the result hash (hex string)."""
    offers = fetch_all_participants(contract)

    if not offers:
        print("No valid participants submitted data.")
        return None

    participant_count = len(offers)
    print(f"Running double auction on {participant_count} participants...")
    matches = greedy_double_auction(offers)

    # Always save to the same folder as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    result_file = os.path.join(script_dir, "match_result.json")
    os.makedirs(os.path.dirname(result_file), exist_ok=True)
    with open(result_file, "w") as f:
        json.dump(matches, f, indent=2)

    print(f"Result written to: {result_file}")

    # Hash result file contents
    with open(result_file, "rb") as f:
        content_bytes = f.read()
        result_hash_hex = keccak(content_bytes).hex()

    print(f"Keccak256 hash of result: 0x{result_hash_hex}")
    return participant_count, result_hash_hex
