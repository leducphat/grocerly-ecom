#!/bin/bash
# =============================================================================
# EC2 First-Time Setup Script
# Run this ONCE on a fresh EC2 instance (Ubuntu) to install Docker
# =============================================================================

set -e

echo "Updating packages..."
sudo apt-get update -y

echo "Installing Docker..."
sudo apt-get install -y docker.io

echo "Installing Docker Compose plugin..."
if ! sudo apt-get install -y docker-compose-plugin; then
	echo "docker-compose-plugin not available, trying docker-compose-v2..."
	sudo apt-get install -y docker-compose-v2
fi

echo "Installing AWS CLI..."
if ! sudo apt-get install -y awscli; then
	echo "awscli package not available, installing AWS CLI v2 from official bundle..."
	sudo apt-get install -y curl unzip
	curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
	unzip -o /tmp/awscliv2.zip -d /tmp
	sudo /tmp/aws/install --update
fi

echo "Adding current user to docker group..."
sudo usermod -aG docker "$(id -un)"

echo "Enabling Docker service..."
sudo systemctl enable docker
sudo systemctl start docker

echo "Creating project directory..."
mkdir -p ~/grocerly

echo ""
echo "============================================"
echo " EC2 setup complete!"
echo " LOG OUT and LOG BACK IN for docker group"
echo " permissions to take effect, then run"
echo " deploy.sh from your local machine."
echo "============================================"
