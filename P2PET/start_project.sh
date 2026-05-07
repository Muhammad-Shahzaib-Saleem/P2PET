#!/bin/bash

# ============================================================
#  P2PET - Full Project Startup Script
#  Run from: P2PET/ (root folder)
#  Usage: bash start_project.sh
# ============================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ROOT_DIR=$(pwd)
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

print_step() {
  echo ""
  echo -e "${CYAN}${BOLD}========================================${NC}"
  echo -e "${CYAN}${BOLD}  $1${NC}"
  echo -e "${CYAN}${BOLD}========================================${NC}"
}

print_ok()    { echo -e "${GREEN}✔ $1${NC}"; }
print_error() { echo -e "${RED}✘ ERROR: $1${NC}"; }
print_warn()  { echo -e "${YELLOW}⚠ $1${NC}"; }
print_info()  { echo -e "${YELLOW}➜ $1${NC}"; }

# ─────────────────────────────────────────────
# Load .env file
# ─────────────────────────────────────────────
ENV_FILE="$ROOT_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
  print_error ".env file not found in $ROOT_DIR"
  print_warn "Create a .env file based on .env.example and fill in your values."
  exit 1
fi

# Export all variables from .env (ignore comments and blank lines)
set -a
source "$ENV_FILE"
set +a

print_ok "Loaded .env file."

# Validate required variables
MISSING=0
for VAR in PI_PASSWORD PI_IPS PI_USER; do
  if [ -z "${!VAR}" ]; then
    print_error "Missing required variable in .env: $VAR"
    MISSING=1
  fi
done
if [ $MISSING -eq 1 ]; then exit 1; fi

# Convert comma-separated PI_IPS string into an array
IFS=',' read -ra PI_IP_ARRAY <<< "$PI_IPS"

PI_REMOTE_DIR="/home/pi/Desktop/P2PET_Dynamic/P2PET/quorum-ibft-chain"

# ─────────────────────────────────────────────
# PREREQUISITES — Clean up local & all Pi nodes
# ─────────────────────────────────────────────
print_step "PREREQUISITES: Cleaning up before starting"

# Check sshpass is installed
if ! command -v sshpass &> /dev/null; then
  print_error "'sshpass' is not installed. Install it with: sudo apt-get install sshpass"
  exit 1
fi

# 1) Run del_junk.sh locally
print_info "Running ./del_junk.sh locally in quorum-ibft-chain..."
cd "$ROOT_DIR/quorum-ibft-chain" || { print_error "Directory 'quorum-ibft-chain' not found!"; exit 1; }

if [ ! -f "./del_junk.sh" ]; then
  print_error "del_junk.sh not found in quorum-ibft-chain/. Aborting."
  exit 1
fi

./del_junk.sh 2>&1 | tee "$LOG_DIR/del_junk_local.log" | sed "s/^/  [Local Cleanup] /"
print_ok "Local cleanup done."

# 2) Run del_junk.sh on each Pi via SSH
echo ""
print_info "Cleaning up ${#PI_IP_ARRAY[@]} Raspberry Pi node(s) via SSH..."
echo ""

PI_FAILED=0
for IP in "${PI_IP_ARRAY[@]}"; do
  echo -ne "  Connecting to ${YELLOW}$PI_USER@$IP${NC}... "

  sshpass -p "$PI_PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
    "$PI_USER@$IP" \
    "cd $PI_REMOTE_DIR && ./del_junk.sh && ./del_junk.sh" \
    2>&1 | tee -a "$LOG_DIR/del_junk_pis.log" | sed "s/^/  [Pi $IP] /"

  SSH_EXIT=${PIPESTATUS[0]}
  if [ $SSH_EXIT -ne 0 ]; then
    print_warn "Could not reach Pi at $IP (skipping — it may be off)"
    PI_FAILED=$((PI_FAILED + 1))
  else
    print_ok "Pi $IP cleaned up (ran del_junk.sh twice)."
  fi
done

if [ $PI_FAILED -gt 0 ]; then
  print_warn "$PI_FAILED Pi(s) were unreachable. Check logs/del_junk_pis.log"
  echo ""
  read -p "$(echo -e ${YELLOW}'Some Pis were unreachable. Continue anyway? (y/n): '${NC})" CONTINUE
  if [[ "$CONTINUE" != "y" && "$CONTINUE" != "Y" ]]; then
    print_error "Aborted by user."
    exit 1
  fi
fi

echo ""
print_ok "Prerequisites done — proceeding to Step 1."

# ─────────────────────────────────────────────
# STEP 1 — Run Blockchain (Quorum IBFT)
# Runs fully and WAITS to complete before Step 2
# ─────────────────────────────────────────────
print_step "STEP 1: Setting up Blockchain (Quorum IBFT)"

cd "$ROOT_DIR/quorum-ibft-chain" || { print_error "Directory 'quorum-ibft-chain' not found!"; exit 1; }

print_info "Running: python initial_validators.py 1"
print_info "Live logs below — waiting for setup to complete..."
echo ""

python initial_validators.py 1 2>&1 | tee "$LOG_DIR/blockchain.log" | sed "s/^/  [Blockchain] /"
BLOCKCHAIN_EXIT=${PIPESTATUS[0]}

echo ""
if [ $BLOCKCHAIN_EXIT -ne 0 ]; then
  print_error "initial_validators.py failed! Check logs/blockchain.log for details. Aborting."
  exit 1
fi
print_ok "Blockchain setup completed successfully — moving to Step 2."

# ─────────────────────────────────────────────
# STEP 2 — Run Quorum Explorer
# ─────────────────────────────────────────────
print_step "STEP 2: Starting Quorum Explorer"

cd "$ROOT_DIR/quorum-ibft-chain/quorum-explorer-master" || { print_error "Directory 'quorum-ibft-chain/quorum-explorer-master' not found!"; exit 1; }

print_info "Checking if port 25000 is already in use..."
PORT_PID=$(lsof -ti :25000 2>/dev/null)
if [ -n "$PORT_PID" ]; then
  print_warn "Port 25000 is in use by PID $PORT_PID — killing it..."
  kill -9 $PORT_PID 2>/dev/null
  sleep 1
  print_ok "Port 25000 freed."
else
  print_ok "Port 25000 is free."
fi

print_info "Running: npm run dev"
print_info "Live logs below (explorer runs in background):"
echo ""

npm run dev 2>&1 | tee "$LOG_DIR/explorer.log" | sed "s/^/  [Explorer] /" &
EXPLORER_PID=$!

echo ""
print_warn "Waiting 10 seconds for Quorum Explorer to initialize..."
for i in $(seq 10 -1 1); do
  echo -ne "  Starting Step 3 in ${BOLD}$i${NC} seconds...\r"
  sleep 1
done
echo ""
print_ok "Explorer started — logs saved to logs/explorer.log"

# ─────────────────────────────────────────────
# STEP 3 — Run Frontend
# ─────────────────────────────────────────────
print_step "STEP 3: Starting Frontend"

cd "$ROOT_DIR/frontend" || { print_error "Directory 'frontend' not found!"; exit 1; }

# Check Node version
CURRENT_NODE=$(node -v 2>/dev/null | sed 's/v//' | cut -d'.' -f1)

if [ -z "$CURRENT_NODE" ]; then
  print_warn "Node.js not found. Attempting to switch to Node 22 via nvm..."
  NEED_NVM=true
elif [ "$CURRENT_NODE" -lt 22 ]; then
  print_warn "Node version is v$CURRENT_NODE (< 22). Switching to Node 22 via nvm..."
  NEED_NVM=true
else
  print_ok "Node version is v$CURRENT_NODE — OK, no switch needed."
  NEED_NVM=false
fi

if [ "$NEED_NVM" = true ]; then
  export NVM_DIR="$HOME/.nvm"
  if [ -s "$NVM_DIR/nvm.sh" ]; then
    source "$NVM_DIR/nvm.sh"
    # --delete-prefix fixes the .npmrc globalconfig/prefix conflict
    nvm use --delete-prefix 22
    if [ $? -ne 0 ]; then
      print_error "Failed to switch to Node 22. Make sure it is installed: nvm install 22"
      kill $EXPLORER_PID 2>/dev/null
      exit 1
    fi
    print_ok "Switched to Node 22 via nvm."
  else
    print_error "nvm not found at $NVM_DIR/nvm.sh. Please install nvm or manually switch to Node 22."
    kill $EXPLORER_PID 2>/dev/null
    exit 1
  fi
fi

echo ""
print_warn "Frontend needs sudo. Please enter your system password:"
sudo -v
if [ $? -ne 0 ]; then
  print_error "sudo authentication failed."
  kill $EXPLORER_PID 2>/dev/null
  exit 1
fi
print_ok "sudo authenticated."

echo ""
print_info "Running: sudo npm run dev"
echo ""
sudo npm run dev 2>&1 | tee "$LOG_DIR/frontend.log" | sed "s/^/  [Frontend] /" &
FRONTEND_PID=$!

sleep 2
echo ""
print_ok "Frontend started — logs saved to logs/frontend.log"

# ─────────────────────────────────────────────
# STEP 4 — Compile & Deploy Smart Contract
# ─────────────────────────────────────────────
print_step "STEP 4: Compiling & Deploying Smart Contract"

cd "$ROOT_DIR/p2p-energy-trading-contract/scripts" || { print_error "Directory 'p2p-energy-trading-contract/scripts' not found!"; exit 1; }

print_info "Running: python compile_contract.py"
echo ""
python compile_contract.py 2>&1 | tee "$LOG_DIR/compile.log" | sed "s/^/  [Compile] /"
COMPILE_EXIT=${PIPESTATUS[0]}

echo ""
if [ $COMPILE_EXIT -ne 0 ]; then
  print_error "compile_contract.py failed! Check logs/compile.log for details. Aborting."
  kill $EXPLORER_PID $FRONTEND_PID 2>/dev/null
  sudo kill $FRONTEND_PID 2>/dev/null
  exit 1
fi
print_ok "Contract compiled successfully."

echo ""
print_info "Running: python deploy_contract.py"
echo ""
python deploy_contract.py 2>&1 | tee "$LOG_DIR/deploy.log" | sed "s/^/  [Deploy] /"
DEPLOY_EXIT=${PIPESTATUS[0]}

echo ""
if [ $DEPLOY_EXIT -ne 0 ]; then
  print_error "deploy_contract.py failed! Check logs/deploy.log for details. Aborting."
  kill $EXPLORER_PID $FRONTEND_PID 2>/dev/null
  sudo kill $FRONTEND_PID 2>/dev/null
  exit 1
fi
print_ok "Contract deployed successfully — moving to Step 5."

# ─────────────────────────────────────────────
# STEP 5 — Run API (python main.py)
# ─────────────────────────────────────────────
print_step "STEP 5: Starting API (python main.py)"

cd "$ROOT_DIR/p2p-energy-trading-contract/api" || { print_error "Directory 'p2p-energy-trading-contract/api' not found!"; exit 1; }

print_info "Running: python main.py"
print_info "Live logs below (API runs in background):"
echo ""

python main.py 2>&1 | tee "$LOG_DIR/api.log" | sed "s/^/  [API] /" &
API_PID=$!

sleep 3
echo ""
print_ok "API started — logs saved to logs/api.log"

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}============================================${NC}"
echo -e "${GREEN}${BOLD}  All services are up and running!${NC}"
echo -e "${GREEN}${BOLD}============================================${NC}"
echo -e "  Prerequisites        ->  logs/del_junk_local.log & logs/del_junk_pis.log  ${GREEN}(completed)${NC}"
echo -e "  Blockchain           ->  logs/blockchain.log   ${GREEN}(setup completed)${NC}"
echo -e "  Explorer    PID: ${YELLOW}$EXPLORER_PID${NC}   ->  logs/explorer.log"
echo -e "  Frontend    PID: ${YELLOW}$FRONTEND_PID${NC}   ->  logs/frontend.log"
echo -e "  Compile              ->  logs/compile.log      ${GREEN}(completed)${NC}"
echo -e "  Deploy               ->  logs/deploy.log       ${GREEN}(completed)${NC}"
echo -e "  API         PID: ${YELLOW}$API_PID${NC}        ->  logs/api.log"
echo ""
echo -e "${CYAN}Live logs are prefixed with their service name in the terminal.${NC}"
echo -e "${CYAN}Press Ctrl+C to stop ALL running services at once.${NC}"
echo ""

# ─────────────────────────────────────────────
# Cleanup on Ctrl+C
# ─────────────────────────────────────────────
cleanup() {
  echo ""
  echo -e "${RED}${BOLD}Stopping all services...${NC}"
  kill $EXPLORER_PID $FRONTEND_PID $API_PID 2>/dev/null
  sudo kill $FRONTEND_PID 2>/dev/null
  print_ok "All services stopped. Goodbye!"
  exit 0
}

trap cleanup SIGINT SIGTERM

# Keep script alive
wait