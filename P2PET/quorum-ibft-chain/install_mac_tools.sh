set -e  # Exit on error

# Define shell config file based on default macOS shell
SHELL_CONFIG="$HOME/.zprofile"
touch "$SHELL_CONFIG"

# ========== Install Homebrew if not present ==========
if ! command -v brew &>/dev/null; then
 echo "Installing Homebrew..."
 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
 echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$SHELL_CONFIG"
 eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# ========== Install dependencies ==========
brew update
brew install curl jq git make python3
brew unlink go
brew install go@1.21
brew link --force go@1.21

# ========== Setup Go path ==========
if ! command -v go &>/dev/null; then
 echo "Go installation failed or not in PATH."
else
 echo "Go is installed at: $(which go)"
 echo 'export PATH="/usr/local/go/bin:$PATH"' >> "$SHELL_CONFIG"
fi







# ========== Install Quorum ==========
if ! command -v geth &>/dev/null; then
 echo "Installing Quorum..."
#  git clone https://github.com/Consensys/quorum.git
#  cd quorum && git checkout v23.4.0 && make all


# -----------------------
# CONFIG
QUORUM_VERSION="v23.4.0"
# -----------------------

# Function to detect OS
detect_os() {
   unameOut="$(uname -s)"
   case "${unameOut}" in
       Linux*)     os=Linux;;
       Darwin*)    os=Mac;;
       *)          os="UNKNOWN:${unameOut}"
   esac
   echo ${os}
}

# Function to switch Go version on macOS
switch_go_mac() {
   local target_version=$1
   echo "Switching Go to version ${target_version}..."
   brew unlink go || true
   brew install go@${target_version} || true
   brew link --force --overwrite go@${target_version}
}

# Detect OS
OS_TYPE=$(detect_os)
echo "Detected OS: $OS_TYPE"

# Store original Go version
ORIGINAL_GO=$(go version | awk '{print $3}' | sed 's/go//')
echo "Current Go version: $ORIGINAL_GO"

# If Mac and Quorum v23.4.0, switch to Go 1.21
if [ "$OS_TYPE" = "Mac" ] && [ "$QUORUM_VERSION" = "v23.4.0" ]; then
   switch_go_mac "1.21"
elif [ "$OS_TYPE" = "Linux" ] && [ "$QUORUM_VERSION" = "v23.4.0" ]; then
   echo "⚠ On Linux: please manually install Go 1.21 before building Quorum v23.4.0."
fi

# Clone and build Quorum
echo "Cloning Quorum $QUORUM_VERSION..."
git clone https://github.com/Consensys/quorum.git
cd quorum
git checkout $QUORUM_VERSION
make all

# Switch back to original Go (Mac only)
if [ "$OS_TYPE" = "Mac" ]; then
   echo "Restoring original Go version $ORIGINAL_GO..."
   brew unlink go
   brew link --force --overwrite go@${ORIGINAL_GO%.*}
fi

echo "✅ Quorum $QUORUM_VERSION installed successfully!"


 cd ..
mkdir -p quorum_bins
cp quorum/build/bin/* quorum_bins

# Ensure no old quorum_bins remains in /usr/local
sudo rm -rf /usr/local/quorum_bins
sudo mv quorum_bins /usr/local/
else
 echo "geth is already present in: $(which geth)"
fi

# ========== Install istanbul-tools ==========
if ! command -v istanbul &>/dev/null; then
 echo "Installing istanbul-tools..."
 git clone https://github.com/ConsenSys/istanbul-tools.git
 cd istanbul-tools && make
 cd ..
mkdir -p istanbul_tools_bins
 cp istanbul-tools/build/bin/* istanbul_tools_bins

 sudo rm -rf /usr/local/istanbul_tools_bins
 sudo mv istanbul_tools_bins /usr/local/
 echo 'export PATH="/usr/local/istanbul_tools_bins:$PATH"' >> "$SHELL_CONFIG"
else
 echo "istanbul is already present in: $(which istanbul)"
fi

# ========== Install Python packages ==========
pip3 install --upgrade pip
pip3 install modbus_tk pyserial pymodbus pexpect eth_utils web3 flask flask-socketio py-solc-x

# ========== Install Node.js modules ==========
sudo npm install express socket.io

## ========== Final setup ==========
#echo "Finalizing shell environment..."
#source "$SHELL_CONFIG"

echo ""
echo "✅ All tools installed successfully on macOS!"
echo ""

#!/bin/bash