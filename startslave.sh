#!/bin/bash

# Define variables
HOSTNAME=$(hostname)
USER=$HOSTNAME  # Use hostname as the user
VENV_DIR="/opt/sys_venv"
GIT_DIR="/home/$USER/_GitHub/PiVortex"
REQUIREMENTS_FILE="requirements.txt"
SLAVE_SCRIPT="slave.py"

# Ensure Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 could not be found. Please install Python 3 and try again."
    exit 1
fi

# Pull the latest changes from the Git repository
if [ -d "$GIT_DIR" ]; then
    echo "Pulling latest changes from Git for $USER..."
    cd "$GIT_DIR" || exit 1
    git pull || { echo "Git pull failed!"; exit 1; }
else
    echo "Error: Git directory $GIT_DIR does not exist for $USER. Please ensure the repository is cloned."
    exit 1
fi

# Create a virtual environment in /opt if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    sudo python3 -m venv "$VENV_DIR" || { echo "Failed to create virtual environment in /opt."; exit 1; }
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate" || { echo "Failed to activate virtual environment."; exit 1; }

# Check if requirements.txt exists in the Git directory
if [ ! -f "$GIT_DIR/$REQUIREMENTS_FILE" ]; then
    echo "Error: $REQUIREMENTS_FILE not found in $GIT_DIR. Please ensure it exists."
    deactivate
    exit 1
fi

# Install requirements
echo "Installing requirements for $USER..."
pip install --upgrade pip
pip install -r "$GIT_DIR/$REQUIREMENTS_FILE" || { echo "Failed to install dependencies."; deactivate; exit 1; }

# Check if the slave script exists in the Git directory
if [ ! -f "$GIT_DIR/$SLAVE_SCRIPT" ]; then
    echo "Error: $SLAVE_SCRIPT not found in $GIT_DIR. Please ensure it exists."
    deactivate
    exit 1
fi

# Start the slave script in the background
echo "Starting the slave program for $USER..."
nohup python "$GIT_DIR/$SLAVE_SCRIPT" >/dev/null 2>&1 &

# Confirm success
echo "Slave program is now running in the background for $USER."
