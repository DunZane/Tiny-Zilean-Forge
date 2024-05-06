#!/bin/bash

# Ensure no other instance of the Python script is running
if pgrep -f "/root/anaconda3/envs/DL/bin/python3.8 main.py --metric processes" > /dev/null; then
  echo "Another instance of the process is already running. Exiting."
  exit 1
fi

# Get current readable timestamp
timestamp=$(date +"%Y-%m-%d_%H-%M-%S")

# Set Zilean-Forge directories
forge_dir="/root/PycharmProjects/Tiny-Zilean-Forge"
logs_dir="$forge_dir/logs"
config_dir="$forge_dir/config"
storage_dir="$forge_dir/storage"

# Create directories if they don't exist
mkdir_if_not_exists() {
  if [ ! -d "$1" ]; then
    mkdir -p "$1" || { echo "Failed to create directory: $1"; exit 1; }
  fi
}

# Create necessary directories
mkdir_if_not_exists "$logs_dir"
mkdir_if_not_exists "$config_dir"
mkdir_if_not_exists "$storage_dir"

# Change to the appropriate directory
cd "$forge_dir" || { echo "Failed to change directory: $forge_dir"; exit 1; }

# Define cleanup actions when the script exits
cleanup() {
  pkill stress-ng  # Kill stress-ng process
}

# Trap EXIT signal to execute cleanup function
trap cleanup EXIT

# Define function to start Python script
start_python_script() {
  while true; do
    # Start Python script in background
    /root/anaconda3/envs/DL/bin/python3.8 main.py --metric processes &
    python_pid=$!  # Get Python process PID
    wait $python_pid  # Wait for Python process to finish
    python_exit_status=$?  # Save Python process exit status
    if [ $python_exit_status -eq 0 ]; then
      break
    else
      echo "Python script exited with an error. Restarting in 5 minutes..."
      # Cleanup residual processes
      pkill -f "/root/anaconda3/envs/DL/bin/python3.8 main.py --metric processes"
      pkill stress-ng
      sleep 300  # Wait 5 minutes before restarting
    fi
  done
}

# Start Python script
start_python_script
