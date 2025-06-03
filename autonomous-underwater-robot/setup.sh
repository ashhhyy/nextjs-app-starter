#!/bin/bash

echo "Setting up Autonomous Underwater Robot..."

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "Warning: This script is designed for Raspberry Pi. Some features may not work on other systems."
fi

# Create virtual environment and install Python dependencies
echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Setup web dashboard
echo "Setting up web dashboard..."
cd web-dashboard
npm install

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p images
mkdir -p logs

# Configure permissions for hardware access
echo "Configuring hardware permissions..."
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
    sudo usermod -a -G gpio,i2c,spi $USER
    
    # Reload modules
    sudo modprobe i2c-dev
    sudo modprobe spi-dev
fi

# Create systemd service for auto-start (only on Raspberry Pi)
if grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "Creating systemd service..."
    sudo tee /etc/systemd/system/underwater-robot.service > /dev/null << EOL
[Unit]
Description=Autonomous Underwater Robot Service
After=network.target

[Service]
ExecStart=$(pwd)/venv/bin/python $(pwd)/rpi/app.py
WorkingDirectory=$(pwd)
User=$USER
Environment=PYTHONPATH=$(pwd)
Restart=always

[Install]
WantedBy=multi-user.target
EOL

    # Enable and start service
    sudo systemctl enable underwater-robot
    sudo systemctl start underwater-robot
fi

echo "Setup complete!"
echo "To start the application:"
echo "1. Flask API: source venv/bin/activate && python rpi/app.py"
echo "2. Web Dashboard: cd web-dashboard && npm start"
