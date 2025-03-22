#!/bin/bash
if [ ! -d "./myenv" ]; then
    echo "Extracting myenv.zip..."
    unzip myenv.zip -d .
fi
# Function to install PHP if not found
install_php() {
    echo "PHP is required but not installed."
    read -p "Do you want to install PHP? (y/n): " choice
    if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
        sudo apt update && sudo apt install -y php
        if command -v php &>/dev/null; then
            echo "PHP installed successfully."
        else
            echo "Failed to install PHP. Please install it manually."
            exit 1
        fi
    else
        echo "PHP installation skipped. Exiting."
        exit 1
    fi
}

# Check if PHP is installed
echo "checking for php"
if ! command -v php &>/dev/null; then
    install_php
fi

# Activate Python virtual environment
echo "activating Virtul env"
if [ -d "./myenv" ]; then
    source ./myenv/bin/activate
else
    echo "Virtual environment not found. Please create one first."
    exit 1
fi

# Install Python dependencies
echo "checking dependencies"
pip install -r requirements.txt

# Start PHP server in the background
echo "starting server"
php -S localhost:8000 &

# Run Python GUI
python GUI/main.py
