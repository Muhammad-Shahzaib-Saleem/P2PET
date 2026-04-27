#!/bin/bash

echo "Switching to DASHBOARD mode..."

# Stop desktop
sudo systemctl stop lightdm

# Kill framebuffer copy
sudo killall fbcp 2>/dev/null

# Small delay
sleep 1

# Run your dashboard
python /home/pi/Desktop/P2PET_Dynamic/P2PET/p2p-energy-trading-contract/api/energy_display.py
