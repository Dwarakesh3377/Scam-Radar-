#!/bin/bash
# Basic Firewall Rules for Scam Detection Server

# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH
ufw allow ssh

# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow Flask Backend (local/docker only usually)
# ufw allow 5000/tcp

# Enable Firewall
ufw --force enable

echo "Firewall rules applied successfully."
