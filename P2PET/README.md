# P2P Energy Trading Platform

A modular, full-stack solution for Peer-to-Peer energy trading, integrating blockchain (Quorum IBFT), IoT energy metering, and a modern web dashboard. This platform enables secure, decentralized, and transparent energy transactions among users.

---

## Features

- **Blockchain-backed market:** Secure, auditable trades using smart contracts.
- **User dashboard:** Intuitive React web app for registering, submitting, and analyzing trades.
- **Hardware/device integration:** Real-time energy data collection from power meters.
- **Node/explorer suite:** Network analytics via Blockscout & Quorum Explorer.
- **Stress tests & profiling:** Tooling for performance benchmarking and TPS metrics.

---

## How to Run This Project (Step-by-Step)

Follow these steps for a full local+distributed testbed deployment, including the blockchain, explorer, smart contract, API, and front-end UI:

**1. Initialize Blockchain Nodes**

- Go to `quorum-ibft-chain` directory.
- Run the following on your main machine to initialize and launch nodes on all Raspberry Pis listed in `ip_dict` (must have SSH access):
  ```bash
  python initial_validators.py 1
  ```
- After a successful run, you will see `node0` through `node9` folders created (one per node).

**2. Start and Configure the Blockchain Explorer**

- Go to the `quorum-explorer-master` directory.
- Edit `src/config/config.json` with your node names and RPC URLs as per your network and follow the README in this folder for other settings.
- Start the explorer:
  ```bash
  npm install
  npm run dev
  ```
- A web UI should open that lets you monitor the live Quorum blockchain and its nodes.

**3. Deploy the Smart Contract**

- Go to `trading-contract/scripts`:
  ```bash
  python compile_contract.py
  python deploy_contract.py
  ```
- After deployment, a transaction for the contract deployment will appear in your running blockchain explorer interface.

**4. Start the API Service**

- Go to `trading-contract/api/`:
  ```bash
  python main.py
  ```
- The script will show you the running API URL (by default, localhost and network IP on port 8000).

**5. Configure API Endpoint for the Frontend**

- Go to `frontend/src/api/` and verify that API calls are using the correct backend URL. Adjust the URL as needed (e.g., localhost or network IP of the machine running the API service).

**6. Start the Frontend Application**

- From the `frontend` directory, run:
  ```bash
  npm install
  npm run dev
  ```
- The React web frontend will now be running (typically on `http://localhost:5173`) and integrated with your backend and blockchain.

You should now have a fully functional P2P Energy Trading Platform running across your blockchain network, explorer, backend APIs, and frontend UI.

---

## Tech Stack

- **Frontend:** React + Vite (JS)
- **Backend API:** Python, FastAPI, Web3.py
- **Smart Contracts:** Solidity (Quorum IBFT, Ethereum-compatible)
- **Power Meter Interface:** Python, custom scripts
- **Explorers/Profiling:** Blockscout, Quorum Explorer, JMeter

---

## Quickstart

### 1. Environment Prerequisites

- **Python 3.9+**, **pip** (for backend/API)
- **Node.js**, **npm** (for frontend)
- **Docker** (for Quorum, explorers)
- (Optional) **Raspberry Pi** or **physical power meter** for live data

### 2. Getting It Running (Development)

```bash
# 1. Set up Python backend
cd trading-contract/api
pip install -r ../../requirments.txt
python main.py

# 2. Set up React frontend
cd ../../frontend
npm install
npm run dev
# visit http://localhost:5173

# 3. Start blockchain (example for node0)
cd ../../quorum-ibft-chain/node0
./startnode0.sh

# 4. Deploy Smart Contract
# (See trading-contract/scripts/ for deployment scripts)
```

You can launch explorers and profiling tools via their respective README files.

---

## Folder Structure & Key Components

```
P2PET_Dynamic/
│
├── frontend/                  # React web app
│   ├── src/                   # Pages, components, api calls, assets
│   └── public/                # Static files (images, favicon)
│
├── trading-contract/          # Smart contracts and blockchain API
│   ├── contracts/             # Solidity source
│   ├── api/                   # FastAPI (Python) backend
│   ├── scripts/               # Deploy & utility scripts
│
├── quorum-ibft-chain/         # Blockchain infra
│   ├── node0/..node9/         # Quorum node setup (keys, genesis, data)
│   ├── blockscout/            # Block explorer (EVM, Docker/Elixir)
│   ├── quorum-explorer-master/# Lightweight Quorum explorer (Node)
│   └── quorum-profiling/      # Profiling & test tools (JMeter, metrics)
│
├── power-interface/           # Python scripts for power meter interfacing
│   ├── pzem.py                # Reads metrics in CLI
│   ├── pzem_gui.py            # GUI display for live data
│   └── AC_COMBOX.py           # Power meter driver logic
│
└── requirments.txt            # Python deps list (for pip)
```

---

## Detailed Directory and File Descriptions

### frontend/ — React Web Application

**src/**

- `api/`: JS files for backend API calls (`api.js`, `energy.js`).
- `assets/`: Images, SVGs, and sample data used in the UI.
- `components/`: Modular UI components, grouped by feature.
  - e.g., `Auth/`, `Energy/`, `NavBar/`, `Sidebar/`, `AddMeterModal/`, etc. Each with their own JSX & CSS files.
- `pages/`: Main route/view React pages (e.g. `AdminDashboardPage.jsx`, `UserLogin.jsx`).
- `App.jsx`, `main.jsx`: App entry/routing setup.
- `index.css`, `App.css`: Global and app styles.
- `dist/`: Production build output (auto-generated).
- `public/`: Static assets.
- `package.json`, `vite.config.js`, `eslint.config.js`: Build & linting configs.

### trading-contract/ — Smart Contracts & Backend API

- `contracts/`: `EnergyTrade.sol` - Solidity smart contract.
- `compiled/`: ABI and bytecode for deployed contracts.
- `deployed/`: Deployed contract addresses and node Pi details.
- `config/`: Participant configuration scripts/data.
- `api/`: Python FastAPI backend, e.g., `main.py` for REST endpoints, blockchain orchestration, and dashboarding; includes logic for registration, data submission, trading, phase and round management.
- `scripts/`: Deployment, compilation, transaction, and testing helpers. Includes `compile_contract.py`, `deploy_contract.py`, `decrypt_key.py`, `matching.py`, etc.

### power-interface/ — Power Meter Interface

- `pzem.py`: Simple CLI-sampled meter reading.
- `pzem_gui.py`: GUI for live meter readings via Tkinter.
- `AC_COMBOX.py`, `w3080.py`: Serial communication drivers.
- `power_checks.py`, `pzem_reset_energy.py`: Utilities for diagnostics/reset.

### quorum-ibft-chain/ — Blockchain Infrastructure

- `node0/`..`node9/`: Each a full blockchain node with `genesis.json`, key configs, chain data, and individual start scripts (`startnodeN.sh`).
- `blockscout/`: Full-featured EVM explorer (Elixir/Phoenix), with all code, configs, and Docker setups.
- `quorum-explorer-master/`: Lightweight Node.js/Next.js explorer for Quorum chains, with config, public, and source directories.
- `quorum-profiling/`: JMeter-based network profiling and TPS monitoring (scripts, dashboards, images, data).
- `initial_validators.py`: Script for initializing validator nodes for the network.

  - **Purpose and Workflow:**
    - This script automates the process of bootstrapping a set of validator nodes for your Quorum IBFT blockchain network.
    - **Mode Selection:**
      - The script takes a single argument: `0` for local (run all nodes on one machine), or `1` for Raspberry Pi distributed mode (distributes nodes remotely via SSH/SCP using their IPs from the script).
    - **Major Steps:**
      1. Sets up node folders and IP mapping (`nodes_to_run`, `ip_dict`).
      2. Runs Istanbul tools to generate validator keys, genesis files, and static nodes config.
      3. Creates an Ethereum account per node and inserts their addresses into the genesis allocation for starting funds.
      4. Updates config files with the correct IPs and ports.
      5. Initializes the `geth` datadir and copies all node data.
      6. Writes a startup script (`startnodeN.sh`) for each node, with appropriate per-node flags for mining, RPC, network, APIs.
      7. In Pi mode, uses helper utilities to copy and launch each node remotely on its host Pi over the network.
      8. Cleans up temporary files afterward.
    - **Cleanup/Retry:** If initialization fails or needs to be re-run for any reason, first run `./del_junk.sh` to remove nodes/data, then re-run `initial_validators.py` in your chosen environment (local or Raspberry Pi mode):
      ```bash
      ./del_junk.sh
      python initial_validators.py 0  # or 1 for Raspberry Pi
      ```
    - **What This Enables:** Reproducible, automated, multi-node Quorum IBFT cluster setup for both local and distributed/hardware testbed experiments.
    - For further details, review the code and comments in `initial_validators.py` and `functions.py`.
  - **How to Use:**
    - **Local (development) mode:**
      ```bash
      python initial_validators.py 0
      ```
      This runs validator initialization entirely on your local machine.
    - **Raspberry Pi distributed mode:**
      ```bash
      python initial_validators.py 1
      ```
      This distributes node folders and starts nodes remotely on Raspberry Pis using the IPs in the script.
  - **If you want to re-run or if initialization fails:**
    1.  First run the cleanup script to remove previous node state:
        ```bash
        ./del_junk.sh
        ```
    2.  Then re-run `initial_validators.py` in your desired environment:
        - For local setup:
          ```bash
          python initial_validators.py 0
          ```
        - For Raspberry Pi distributed setup:
          ```bash
          python initial_validators.py 1
          ```

- `functions.py`, `extract_private_key.py`: Keychain, deployment, and node utilities.
- `del_junk.sh`, `install_mac_tools.sh`, `install_ubuntu_tools.sh`: Maintenance and setup scripts.
- `validators.log`, `geth_accounts_info.log`: Operational logs.

---

## Customization & Extensions

- Add new smart contract logic in `trading-contract/contracts/`.
- Expand API endpoints in `trading-contract/api/`.
- Extend dashboard functionality in `frontend/src/`.

---

## Documentation & Support

- For detailed blockchain explorer usage, consult the README files in `blockscout`, `quorum-explorer-master`, and `quorum-profiling`.
- API and trading logic are documented with inline docstrings and comments.
- For issues or enhancements, open GitHub Issues or PRs!

---

## License

MIT (platform code) + GPLv3 (Blockscout)

## Complete Folder and File Listing

Below is an expanded structure, including main subfolders and key files for reference.

### frontend/

- **src/**
  - **api/**
    - api.js
    - energy.js
  - **assets/**
    - admin.png
    - energySample.json
    - react.svg
    - user.png
  - **components/**
    - **AddMeterModal/**
      - AddMeterModal.css
      - AddMeterModal.jsx
    - **AdminDashboard/**
      - AdminDashboard.css
      - AdminDashboard.jsx
    - **AdvancePhase/**
      - AdvancePhaseForm.css
      - AdvancePhaseForm.jsx
    - **Auth/**
      - Auth.css
      - LoginForm.jsx
      - SignupForm.jsx
    - **Button/**
      - Button.css
      - Button.jsx
    - **Energy/**
      - **ChartsTabs/**
        - ChartBase.jsx
        - ChartsTabs.css
        - ChartsTabs.jsx
        - EnergyDualBar.jsx
        - EnergyHourlyModal.jsx
      - **CostPredictedCard/**
        - CostPredictedCard.css
        - CostPredictedCard.jsx
      - **CustomerCard/**
        - CustomerCard.css
        - CustomerCard.jsx
      - **EnergyDashboardView/**
        - EnergyDashboardView.css
        - EnergyDashboardView.jsx
      - **shared/**
        - chartTheme.js
    - **HashParticipant/**
      - HashParticipantForm.css
      - HashParticipantForm.jsx
    - **Home/**
      - Home.css
      - Home.jsx
    - **MeterTable/**
      - MeterTable.css
      - MeterTable.jsx
    - **NavBar/**
      - Navbar.css
      - Navbar.jsx
    - **Register/**
      - RegisterForm.css
      - RegisterForm.jsx
    - **SearchBar/**
      - SearchBar.css
      - SearchBar.jsx
    - **Sidebar/**
      - Sidebar.css
      - Sidebar.jsx
    - **StatusPanel/**
      - StatusPanel.css
      - StatusPanel.jsx
    - **SubmitExecutionResultForm/**
      - SubmitExecutionResultForm.css
      - SubmitExecutionResultForm.jsx
    - **Trade/**
      - TradeForm.css
      - TradeForm.jsx
    - **VerifyExecutionResultForm/**
      - VerifyExecutionResultForm.css
      - VerifyExecutionResultForm.jsx
    - **ViewToggle/**
      - ViewToggle.css
      - ViewToggle.jsx
  - **pages/**
    - AdminDashboardPage.jsx
    - AdminLogin.jsx
    - AdminSignup.jsx
    - AdvancePhase.jsx
    - EnergyDashboard.jsx
    - HashParticipant.jsx
    - HomePage.jsx
    - NetworkStatus.jsx
    - RegisterNode.jsx
    - SubmitData.jsx
    - SubmitExecutionResultPage.jsx
    - UserLogin.jsx
    - UserSignupPage.jsx
    - VerifyExecutionResult.jsx
  - App.css
  - App.jsx
  - index.css
  - main.jsx

---

### trading-contract/

- **api/**
  - cloudflare.log
  - energy_dashboard.py
  - fetch_and_match.py
  - main_controller.py
  - main.py
  - match_result.json
  - matching.py
  - NodeNum.txt
  - pis.json
- **compiled/**
  - EnergyTrade_abi.json
  - EnergyTrade_bytecode.txt
- **config/**
  - participants_data.py
- **contracts/**
  - EnergyTrade.sol
- **deployed/**
  - energy_trade_contract_address.json
  - pis.json
- **scripts/**
  - checking_key_store.py
  - compile_contract.py
  - compiled_P2PEnergyTrading.json
  - decrypt_key.py
  - deploy_contract.py
  - fetch_and_match.py
  - get_account_address.py
  - initiate_transaction.py
  - matching.py
  - register_and_submit.py

---

### quorum-ibft-chain/

- del_junk.sh
- extract_private_key.py
- functions.py
- geth_accounts_info.log
- initial_validators.py
- install_mac_tools.sh
- install_ubuntu_tools.sh
- **node0/** ... **node9/** (folders per node, each with its own data/, genesis.json, istanbul.log, start script, etc.)
- **blockscout/** (EVM explorer—contains many further files/subfolders)
- **quorum-explorer-master/**
  - Dockerfile
  - LICENSE
  - next-env.d.ts
  - next-logger.config.js
  - next.config.js
  - package-lock.json
  - package.json
  - README.md
  - **public/images/**
  - **src/common/**, **src/config/**, **src/pages/**
  - **styles/**
  - tsconfig.json
- **quorum-profiling/**
  - Dockerfile_jmeter
  - **images/**
  - **jmeter-test/**
  - **scripts/**
  - **stresstest-aws/**
  - **tps-monitor/**

---

### power-interface/

- AC_COMBOX.py
- power_checks.py
- pzem_gui.py
- pzem_reset_energy.py
- pzem.py
- w3080.py
