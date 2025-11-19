# from web3 import Web3
# from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
# import pandas as pd
# import time
# import os

# # ==============================
# # Configuration
# # ==============================
# RPC_URL = "http://100.116.162.18:22000"
# BLOCKS_CSV = "quorum_blocks.csv"
# TXS_CSV = "quorum_transactions.csv"
# SLEEP_SECONDS = 5  # check every 5 seconds
# # ==============================

# # Connect to your local Quorum RPC endpoint
# web3 = Web3(Web3.HTTPProvider(RPC_URL))

# if not web3.is_connected():
#     raise Exception("❌ Unable to connect to Quorum RPC. Check your node URL.")

# # Inject POA middleware (required for Quorum / Clique)
# web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# print("✅ Connected to Quorum node")

# def fetch_block(block_number):
#     """Fetch a single block and its transactions"""
#     block = web3.eth.get_block(block_number, full_transactions=True)

#     block_info = {
#         "number": block.number,
#         "hash": block.hash.hex(),
#         "miner": block.miner,
#         "timestamp": block.timestamp,
#         "gasUsed": block.gasUsed,
#         "transactions": len(block.transactions)
#     }

#     tx_list = []
#     for tx in block.transactions:
#         tx_list.append({
#             "blockNumber": block.number,
#             "hash": tx.hash.hex(),
#             "from": tx["from"],
#             "to": tx["to"],
#             "value": tx["value"],
#             "gas": tx["gas"],
#             "gasPrice": tx["gasPrice"]
#         })

#     return block_info, tx_list

# def append_to_csv(data, filename):
#     """Append a list of dicts to CSV file"""
#     df = pd.DataFrame(data)
#     header = not os.path.exists(filename)
#     df.to_csv(filename, mode="a", index=False, header=header)

# def continuous_fetch():
#     """Continuously fetch and append new blocks"""
#     latest_saved = 0
#     if os.path.exists(BLOCKS_CSV):
#         df = pd.read_csv(BLOCKS_CSV)
#         if not df.empty:
#             latest_saved = int(df["number"].max())

#     print(f"🚀 Starting from block {latest_saved + 1}")

#     while True:
#         try:
#             current_block = web3.eth.block_number

#             if current_block > latest_saved:
#                 for block_num in range(latest_saved + 1, current_block + 1):
#                     block_info, txs = fetch_block(block_num)
#                     append_to_csv([block_info], BLOCKS_CSV)
#                     append_to_csv(txs, TXS_CSV)
#                     print(f"✅ Saved block {block_num} with {len(txs)} txs")

#                     latest_saved = block_num
#             else:
#                 print("⏳ No new blocks yet...")

#             time.sleep(SLEEP_SECONDS)

#         except Exception as e:
#             print(f"⚠️ Error: {e}")
#             time.sleep(5)

# if __name__ == "__main__":
#     continuous_fetch()

# from web3 import Web3
# from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
# import pandas as pd
# import time
# import os
# from datetime import datetime

# # ==============================
# # Configuration
# # ==============================
# RPC_URL = "http://100.116.162.18:22000"  # your local Quorum RPC
# TXS_CSV = "quorum_transactions.csv"
# SLEEP_SECONDS = 5  # check every 5 seconds
# # ==============================

# # Connect to your local Quorum RPC endpoint
# web3 = Web3(Web3.HTTPProvider(RPC_URL))

# if not web3.is_connected():
#     raise Exception("❌ Unable to connect to Quorum RPC. Check your node URL.")

# # Inject POA middleware (required for Quorum / Clique)
# web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# print("✅ Connected to Quorum node")


# def fetch_block(block_number):
#     """Fetch block and transaction details with full transaction info"""
#     block = web3.eth.get_block(block_number, full_transactions=True)

#     block_number = block.number
#     miner = block.miner
#     block_hash = block.hash.hex()
#     tx_count = len(block.transactions)
#     uncles = len(block.uncles)
#     size = block.size
#     gas_used = block.gasUsed
#     timestamp = datetime.fromtimestamp(block.timestamp).strftime("%Y-%m-%d %H:%M:%S")

#     tx_list = []

#     if tx_count == 0:
#         # Still save block even if no transactions
#         tx_list.append({
#             "Block Number": block_number,
#             "Miner": miner,
#             "Block Hash": block_hash,
#             "Transaction Count": tx_count,
#             "Uncles": uncles,
#             "Block Size": size,
#             "Gas Used": gas_used,
#             "Timestamp": timestamp,
#             "Tx Hash": "",
#             "From": "",
#             "To": "",
#             "Value (Ether)": "",
#             "Gas": "",
#             "Gas Price (Wei)": ""
#         })
#     else:
#         for tx in block.transactions:
#             tx_list.append({
#                 "Block Number": block_number,
#                 "Miner": miner,
#                 "Block Hash": block_hash,
#                 "Transaction Count": tx_count,
#                 "Uncles": uncles,
#                 "Block Size": size,
#                 "Gas Used": gas_used,
#                 "Timestamp": timestamp,
#                 "Tx Hash": tx.hash.hex(),
#                 "From": tx["from"],
#                 "To": tx["to"] if tx["to"] else "",
#                 "Value (Ether)": float(web3.from_wei(tx["value"], "ether")),
#                 "Gas": tx["gas"],
#                 "Gas Price (Wei)": tx["gasPrice"]
#             })
#     return tx_list


# def append_to_csv(data, filename):
#     """Append a list of dicts to CSV file"""
#     df = pd.DataFrame(data)
#     header = not os.path.exists(filename)
#     df.to_csv(filename, mode="a", index=False, header=header)


# def continuous_fetch():
#     """Continuously fetch and append new block & transaction data"""
#     latest_saved = -1
#     if os.path.exists(TXS_CSV):
#         df = pd.read_csv(TXS_CSV)
#         if not df.empty:
#             latest_saved = int(df["Block Number"].max())

#     print(f"🚀 Starting from block {latest_saved + 1}")

#     while True:
#         try:
#             current_block = web3.eth.block_number

#             if current_block > latest_saved:
#                 for block_num in range(latest_saved + 1, current_block + 1):
#                     txs = fetch_block(block_num)
#                     append_to_csv(txs, TXS_CSV)
#                     print(f"✅ Saved block {block_num} with {len(txs)} txs")
#                     latest_saved = block_num
#             else:
#                 print("⏳ No new blocks yet...")

#             time.sleep(SLEEP_SECONDS)

#         except Exception as e:
#             print(f"⚠️ Error: {e}")
#             time.sleep(5)


# if __name__ == "__main__":
#     continuous_fetch()


from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
import pandas as pd
import time
import os
from datetime import datetime

# ==============================
# Configuration
# ==============================
RPC_URL = "http://100.76.91.82:22000"  # your Quorum RPC endpoint
TXS_CSV = "quorum_transactions.csv"
SLEEP_SECONDS = 5  # check every 5 seconds
# ==============================

# Connect to Quorum RPC
web3 = Web3(Web3.HTTPProvider(RPC_URL))

if not web3.is_connected():
    raise Exception("❌ Unable to connect to Quorum RPC. Check your node URL.")

# Inject POA middleware (required for Quorum / Clique)
web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
print("✅ Connected to Quorum node")


def fetch_block(block_number):
    """Fetch a block with transactions and full metadata"""
    block = web3.eth.get_block(block_number, full_transactions=True)

    block_number = block.number
    miner = block.miner
    block_hash = block.hash.hex()
    tx_count = len(block.transactions)
    uncles = len(block.uncles)
    size = block.size if hasattr(block, "size") else None
    gas_used = block.gasUsed
    timestamp = datetime.fromtimestamp(block.timestamp).strftime("%Y-%m-%d %H:%M:%S")

    tx_list = []

    if tx_count == 0:
        # even if block has no tx, we save metadata
        tx_list.append({
            "Block": block_number,
            "Miner": miner,
            "Hash": block_hash,
            "Transactions": tx_count,
            "Uncles": uncles,
            "Size": size,
            "Gas Used": gas_used,
            "Timestamp": timestamp,
            "Tx Hash": "",
            "From": "",
            "To": "",
            "Value (Ether)": "",
            "Gas": "",
            "Gas Price (Wei)": ""
        })
    else:
        for tx in block.transactions:
            tx_list.append({
                "Block": block_number,
                "Miner": miner,
                "Hash": block_hash,
                "Transactions": tx_count,
                "Uncles": uncles,
                "Size": size,
                "Gas Used": gas_used,
                "Timestamp": timestamp,
                "Tx Hash": tx.hash.hex(),
                "From": tx["from"],
                "To": tx["to"] if tx["to"] else "",
                "Value (Ether)": float(web3.from_wei(tx["value"], "ether")),
                "Gas": tx["gas"],
                "Gas Price (Wei)": tx["gasPrice"]
            })
    return tx_list


def append_to_csv(data, filename):
    """Append list of dicts to CSV"""
    df = pd.DataFrame(data)
    header = not os.path.exists(filename)
    df.to_csv(filename, mode="a", index=False, header=header)


def continuous_fetch():
    """Continuously fetch and append new blocks and transactions"""
    latest_saved = -1
    if os.path.exists(TXS_CSV):
        df = pd.read_csv(TXS_CSV)
        if not df.empty and "Block" in df.columns:
            latest_saved = int(df["Block"].max())

    print(f"🚀 Starting from block {latest_saved + 1}")

    while True:
        try:
            current_block = web3.eth.block_number

            if current_block > latest_saved:
                for block_num in range(latest_saved + 1, current_block + 1):
                    txs = fetch_block(block_num)
                    append_to_csv(txs, TXS_CSV)
                    print(f"✅ Saved block {block_num} | Size: {txs[0]['Size']} | TXs: {len(txs)}")
                    latest_saved = block_num
            else:
                print("⏳ No new blocks yet...")

            time.sleep(SLEEP_SECONDS)

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    continuous_fetch()
