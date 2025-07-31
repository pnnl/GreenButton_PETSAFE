#!/bin/bash

# Check if Python is installed. If not, ask to install it.
install="x" # N/A
command -v python3 >/dev/null 2>&1 || echo -n "Python not installed. Install it? y/n: " && read install
if [ $install == "y" ]; then
    sudo apt install python3
else
    "Cannot perform Python environment setup without Python installed. Exiting."
    return 1
fi

# Check if inside virtual environment; if not, activate one
if [[ $PATH != *".venv/bin"* ]]; then
    # See if one already exists and activate if so
    if [ -f .venv/bin/activate ]; then
        .venv/bin/activate
    else
        # Does not exist; create it
        python -m venv .venv
        .venv/bin/activate
    fi
fi

# Now that we know we have a virtual environment, install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

return 0