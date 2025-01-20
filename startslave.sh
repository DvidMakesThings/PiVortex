#!/bin/bash

# Define variables
VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"
SLAVE_SCRIPT="slave.py"

# Ensure Python 3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 could not be found. Please install Python 3 and try again."
    exit 1
fi

# Create a virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
fi

# Activate the virtual environment
source $VENV_DIR/bin/activate

# Install requirements
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "Creating requirements file..."
    echo "flask" > $REQUIREMENTS_FILE
fi

echo "Installing requirements..."
pip install -r $REQUIREMENTS_FILE

# Start the slave program
echo "Starting the slave program..."
python $SLAVE_SCRIPT &

# Confirm success
echo "Slave program is now running."
