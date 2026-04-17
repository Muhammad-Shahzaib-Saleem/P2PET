#!/bin/bash

echo "Switching to DESKTOP mode..."

# Stop dashboard
sudo pkill -f dashboard.py

# Kill old fbcp
sudo killall fbcp 2>/dev/null

# Start GUI
sudo systemctl start lightdm &

# Start fbcp almost immediately
sleep 1
fbcp &