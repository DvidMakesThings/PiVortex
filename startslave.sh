#!/bin/bash

# Define variables
VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"
SLAVE_SCRIPT="slave.py"

# Ensure Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 could not be found. Please install Python 3 and try again."
    exit 1
fi

# Create a virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Check if requirements.txt exists
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "Error: $REQUIREMENTS_FILE not found. Please create one with the necessary dependencies."
    deactivate
    exit 1
fi

# Install requirements
echo "Installing requirements..."
pip install --upgrade pip
pip install -r "$REQUIREMENTS_FILE"

# Check if the slave script exists
if [ ! -f "$SLAVE_SCRIPT" ]; then
    echo "Error: $SLAVE_SCRIPT not found. Please ensure it exists in the current directory."
    deactivate
    exit 1
fi

# Start the slave script
echo "Starting the slave program..."
nohup python "$SLAVE_SCRIPT" > slave.log 2>&1 &

# Confirm success
echo "Slave program is now running in the background. Logs are being saved to slave.log."
