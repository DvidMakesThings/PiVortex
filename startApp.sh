#!/bin/bash

# Define variables
VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"
SCRIPT="gui_try.py"

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

# Check if the Python script exists
if [ ! -f "$SCRIPT" ]; then
    echo "Error: $SCRIPT not found. Please ensure it exists in the current directory."
    deactivate
    exit 1
fi

# Start the Python script
echo "Starting the master PC program..."
python "$SCRIPT" &

# Confirm success
echo "Master PC program is now running."
