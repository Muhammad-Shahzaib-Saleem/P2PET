import json
from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware

# ===== Configuration =====
RPC_URL = "http://127.0.0.1:22000"
ABI_PATH = "../compiled/EnergyTrade_abi.json"
ADDRESS_PATH = "../deployed/energy_trade_contract_address.json"
PARTICIPANT_DATA_PATH = "../config/participant_data.json"


def connect_web3(rpc_url: str) -> Web3:
    """Connect to Web3 provider with PoA middleware."""
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    if not w3.is_connected():
        raise ConnectionError(f"Unable to connect to RPC at {rpc_url}")
    return w3


def load_contract(w3: Web3, abi_path: str, address_path: str):
    """Load contract instance using ABI and deployed address."""
    with open(abi_path, "r") as abi_file:
        abi = json.load(abi_file)
    with open(address_path, "r") as addr_file:
        contract_address = json.load(addr_file)["contract_address"]
    return w3.eth.contract(address=contract_address, abi=abi)


def load_participant_data(file_path: str):
    """Load participants data from JSON file."""
    with open(file_path, "r") as file:
        return json.load(file)


def send_transaction(w3: Web3, txn_func, from_addr: str, private_key: str):
    """Sign and send a transaction for a contract function call."""
    nonce = w3.eth.get_transaction_count(from_addr)
    txn = txn_func.build_transaction({
        "from": from_addr,
        "nonce": nonce,
        "gas": 500000,
        "gasPrice": w3.to_wei("0", "gwei")  # Quorum often uses 0 gas price
    })
    signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt


def is_registered(contract, address: str) -> bool:
    """Check if participant is already registered."""
    slot = contract.functions.addressToSlot(address).call()
    return slot != 0  # 0 means unregistered in your Solidity code


def register_and_submit(w3: Web3, contract, participant: dict):
    """Register participant if needed, then submit data."""
    addr = participant["address"]
    pk = participant["private_key"]

    # Step 1: Register if not registered
    if not is_registered(contract, addr):
        print(f"📝 Registering {addr}...")
        receipt = send_transaction(w3, contract.functions.register(), addr, pk)
        print(f"✅ Registered in block {receipt.blockNumber}")
    else:
        print(f"ℹ️ {addr} already registered.")

    # Step 2: Submit data
    print(f"📤 Submitting data for {addr}...")
    receipt = send_transaction(
        w3,
        contract.functions.submitData(
            participant["role"],
            participant["energyAmount"],
            participant["pricePerKWh"]
        ),
        addr,
        pk
    )
    print(f"✅ Data submitted in block {receipt.blockNumber}")


if __name__ == "__main__":
    w3 = connect_web3(RPC_URL)
    contract = load_contract(w3, ABI_PATH, ADDRESS_PATH)
    participants = load_participant_data(PARTICIPANT_DATA_PATH)

    for participant in participants:
        try:
            register_and_submit(w3, contract, participant)
        except Exception as e:
            print(f"❌ Error for {participant['address']}: {e}")
