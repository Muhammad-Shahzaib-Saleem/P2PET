# from solcx import compile_source, install_solc
# import json
# import os
#
# # Install Solidity compiler
# install_solc("0.8.0")
#
# with open("../contracts/EnergyTrade.sol", "r") as file:
#     contract_source_code = file.read()
#
# # Compile
# compiled = compile_source(contract_source_code, solc_version="0.8.0")
# _, contract_interface = compiled.popitem()
#
# # Save ABI
# os.makedirs("../compiled", exist_ok=True)
# with open("../compiled/EnergyTrade_abi.json", "w") as abi_file:
#     json.dump(contract_interface['abi'], abi_file)
#
# # Save bytecode
# with open("../compiled/EnergyTrade_bytecode.txt", "w") as bytecode_file:
#     bytecode_file.write(contract_interface['bin'])
#
# print("Compilation complete.")

import os
import json
from solcx import compile_source, install_solc

SOLC_VERSION = "0.8.0"
CONTRACT_PATH = "../contracts/EnergyTrade.sol"
OUTPUT_DIR = "../compiled"
ABI_FILENAME = "EnergyTrade_abi.json"
BYTECODE_FILENAME = "EnergyTrade_bytecode.txt"


def install_compiler(version: str):
    """Install the specified Solidity compiler version."""
    print(f"Installing Solidity compiler {version}...")
    install_solc(version)


def load_contract_source(path: str) -> str:
    """Load the Solidity contract source code from a file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Contract file not found: {path}")
    with open(path, "r") as file:
        return file.read()


def compile_contract(source_code: str, version: str) -> dict:
    """Compile the Solidity contract and return the contract interface."""
    print(f"Compiling contract with solc {version}...")
    compiled = compile_source(source_code, solc_version=version)
    _, contract_interface = compiled.popitem()
    return contract_interface


def save_abi(abi: dict, output_dir: str, filename: str):
    """Save the ABI to a JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, "w") as abi_file:
        json.dump(abi, abi_file)
    print(f"ABI saved to {path}")


def save_bytecode(bytecode: str, output_dir: str, filename: str):
    """Save the bytecode to a text file."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, "w") as bytecode_file:
        bytecode_file.write(bytecode)
    print(f"Bytecode saved to {path}")


def main():
    install_compiler(SOLC_VERSION)
    source_code = load_contract_source(CONTRACT_PATH)
    contract_interface = compile_contract(source_code, SOLC_VERSION)
    save_abi(contract_interface["abi"], OUTPUT_DIR, ABI_FILENAME)
    save_bytecode(contract_interface["bin"], OUTPUT_DIR, BYTECODE_FILENAME)
    print("Compilation complete.")


if __name__ == "__main__":
    main()

