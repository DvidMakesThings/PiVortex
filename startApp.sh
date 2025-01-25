#!/bin/bash

# Define variables
GIT_DIR="/home/masterpi/_GitHub/PiVortex"
VENV_DIR="/opt/sys_venv"
SCRIPT="MasterGui.py"

# Ensure Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 could not be found. Please install Python 3 and try again."
    exit 1
fi

# Step 1: Create a virtual environment in /opt if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating one in $VENV_DIR..."
    sudo python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment in $VENV_DIR."
        exit 1
    fi
    echo "Virtual environment created successfully in $VENV_DIR."
else
    echo "Virtual environment already exists in $VENV_DIR."
fi

# Step 2: Activate the virtual environment
echo "Activating the virtual environment..."
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    echo "Failed to activate the virtual environment."
    exit 1
fi

# Step 3: Navigate to the Git directory
if [ -d "$GIT_DIR" ]; then
    echo "Navigating to $GIT_DIR and pulling the latest changes..."
    cd "$GIT_DIR"
    git pull || { echo "Git pull failed!"; deactivate; exit 1; }
else
    echo "Error: $GIT_DIR not found. Please ensure the repository exists."
    deactivate
    exit 1
fi

# Step 4: Install requirements
REQUIREMENTS_FILE="$GIT_DIR/requirements.txt"
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing requirements from $REQUIREMENTS_FILE..."
    sudo "$VENV_DIR/bin/pip" install --upgrade pip
    sudo "$VENV_DIR/bin/pip" install -r "$REQUIREMENTS_FILE"
    if [ $? -ne 0 ]; then
        echo "Failed to install requirements."
        deactivate
        exit 1
    fi
    echo "Requirements installed successfully."
else
    echo "Error: $REQUIREMENTS_FILE not found in $GIT_DIR."
    deactivate
    exit 1
fi

# Step 5: Check and run the Python script
SCRIPT_PATH="$GIT_DIR/$SCRIPT"
if [ -f "$SCRIPT_PATH" ]; then
    echo "Starting the master PC program..."
    sudo "$VENV_DIR/bin/python" "$SCRIPT_PATH" &
    echo "Master PC program is now running."
else
    echo "Error: $SCRIPT not found in $GIT_DIR."
    deactivate
    exit 1
fi
