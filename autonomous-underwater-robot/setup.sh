#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "------------------------------------------------------------------"
echo "Streamlined Autonomous Underwater Robot Environment Setup (Part 1)"
echo "------------------------------------------------------------------"

# Get the current user
CURRENT_USER=$(whoami)
# Get the Raspberry Pi's primary IP address dynamically
PI_IP=$(hostname -I | awk '{print $1}')

if [ -z "$PI_IP" ]; then
    echo "ERROR: Could not determine Raspberry Pi's IP address. Please ensure it has a network connection."
    echo "Attempting to re-check IP in 10 seconds..."
    sleep 10
    PI_IP=$(hostname -I | awk '{print $1}')
    if [ -z "$PI_IP" ]; then
        echo "FATAL ERROR: Still unable to get IP. Please ensure Raspberry Pi has a stable network connection (Ethernet or Wi-Fi) before running this script."
        exit 1
    fi
fi

echo "Detected Raspberry Pi IP Address: $PI_IP"
echo "Using user: $CURRENT_USER"

# --- 1. System Updates and Package Installations ---
echo ""
echo "--- 1. Updating system and installing essential packages ---"
sudo apt update && sudo apt upgrade -y

echo "Installing git, nodejs, npm, python3-venv, python3-pip, python3-smbus..."
sudo apt install git nodejs npm python3-venv python3-pip python3-smbus -y

# --- 2. Python Backend (Flask API) Environment Setup ---
echo ""
echo "--- 2. Setting up Python environment for Flask API ---"
PYTHON_APP_DIR=$(pwd) # Store current directory (project root)

# Remove old virtual environment if it exists
if [ -d "venv" ]; then
    echo "Removing existing Python virtual environment..."
    rm -rf venv
fi

echo "Creating new Python virtual environment with system site packages..."
python3 -m venv venv --system-site-packages
source venv/bin/activate

echo "Upgrading pip and installing Python dependencies from requirements.txt..."
pip install --upgrade pip

# Check for requirements.txt in the current directory (project root)
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found in $PYTHON_APP_DIR. Installing Flask and Flask-Cors as a fallback."
    pip install Flask Flask-Cors
fi

# --- 3. Configure Flask API for CORS ---
echo ""
echo "--- 3. Configuring Flask API (rpi/app.py) for CORS ---"
FLASK_APP_PATH="rpi/app.py"

# Add 'from flask_cors import CORS' if not present
if ! grep -q "from flask_cors import CORS" "$FLASK_APP_PATH"; then
    sed -i '1ifrom flask_cors import CORS' "$FLASK_APP_PATH"
    echo "Added 'from flask_cors import CORS' to $FLASK_APP_PATH"
fi

# Add 'CORS(app)' after 'app = Flask(__name__)' if not present
if ! grep -q "CORS(app)" "$FLASK_APP_PATH"; then
    sed -i "/app = Flask(__name__)/a CORS(app)" "$FLASK_APP_PATH"
    echo "Added 'CORS(app)' to $FLASK_APP_PATH"
fi

# --- 4. Web Dashboard (Frontend) Dependencies Installation ---
echo ""
echo "--- 4. Installing web dashboard dependencies (npm install) ---"
echo "This may take several minutes. Ensure your web-dashboard files (src/, public/, package.json, etc.) are already in place."
WEB_DASHBOARD_DIR="web-dashboard"

if [ ! -d "$WEB_DASHBOARD_DIR" ]; then
    echo "ERROR: Web dashboard directory '$WEB_DASHBOARD_DIR' not found."
    echo "Please ensure you have cloned your repository and that the 'web-dashboard' folder is present and contains its files before running this script."
    exit 1
fi

cd "$WEB_DASHBOARD_DIR"
npm install
cd .. # Go back to project root

# --- 5. Configure Permissions for Hardware Access ---
echo ""
echo "--- 5. Configuring hardware permissions ---"
# Create necessary directories (if they don't exist in your repo)
echo "Creating necessary directories for logs and images..."
mkdir -p images
mkdir -p logs

if grep -q "Raspberry Pi" /proc/cpuinfo; then
    # Enable I2C if not already enabled
    if ! grep -q "^i2c-dev" /etc/modules; then
        echo "i2c-dev" | sudo tee -a /etc/modules
    fi
    
    # Enable SPI if not already enabled
    if ! grep -q "^spi-dev" /etc/modules; then
        echo "spi-dev" | sudo tee -a /etc/modules
    fi
    
    # Add user to required groups
    echo "Adding user '$CURRENT_USER' to gpio, i2c, spi groups..."
    sudo usermod -a -G gpio,i2c,spi "$CURRENT_USER"
    
    # Reload modules (requires reboot for full effect, especially for user groups)
    echo "Attempting to reload kernel modules (full effect after reboot)..."
    sudo modprobe i2c-dev || echo "Warning: i2c-dev module reload failed. May require reboot."
    sudo modprobe spi-dev || echo "Warning: spi-dev module reload failed. May require reboot."
else
    echo "Not on Raspberry Pi. Skipping hardware permission configuration."
fi

# --- 6. Create Systemd Service for Auto-start (only on Raspberry Pi) ---
echo ""
echo "--- 6. Creating systemd service for Flask API auto-start ---"
if grep -q "Raspberry Pi" /proc/cpuinfo; then
    SERVICE_FILE="/etc/systemd/system/underwater-robot.service"
    echo "Creating systemd service file: $SERVICE_FILE"
    sudo tee "$SERVICE_FILE" > /dev/null << EOL
[Unit]
Description=Autonomous Underwater Robot Service
After=network.target

[Service]
ExecStart=$(pwd)/venv/bin/python $(pwd)/rpi/app.py
WorkingDirectory=$(pwd)
User=$CURRENT_USER
Environment=PYTHONPATH=$(pwd)
Restart=always

[Install]
WantedBy=multi-user.target
EOL

    echo "Enabling and starting systemd service (service will be fully active after reboot)."
    sudo systemctl enable underwater-robot
    sudo systemctl start underwater-robot
else
    echo "Not on Raspberry Pi. Skipping systemd service creation."
fi

echo ""
echo "---------------------------------------------------"
echo "Autonomous Underwater Robot Setup Script Finished!"
echo "---------------------------------------------------"
echo "IMPORTANT NEXT STEPS:"
echo "1. Reboot your Raspberry Pi for all changes (especially group memberships and systemd) to take full effect:"
echo "   sudo reboot"
echo ""
echo "2. After reboot, SSH back into your Pi."
echo ""
echo "3. To run the Flask API (backend) if not auto-started by systemd:"
echo "   cd $PYTHON_APP_DIR"
echo "   source venv/bin/activate"
echo "   python rpi/app.py"
echo "   (Keep this terminal session open or use 'screen'/'tmux')"
echo ""
echo "4. To run the Web Dashboard (frontend):"
echo "   Open a NEW SSH session to your Pi."
echo "   cd $PYTHON_APP_DIR/$WEB_DASHBOARD_DIR"
echo "   npm start"
echo "   (Keep this terminal session open or use 'screen'/'tmux')"
echo ""
echo "5. Access the Web Dashboard from your computer's browser:"
echo "   http://${PI_IP}:3000"
echo "   (Make sure your computer is on the same network as the Pi.)"
echo "---------------------------------------------------"
