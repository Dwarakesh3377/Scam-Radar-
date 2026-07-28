#!/bin/bash
# Basic SSL Configuration Script using Certbot

echo "Setting up SSL with Certbot..."

if ! command -v certbot &> /dev/null
then
    echo "Certbot not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
fi

# Request certificate (uncomment and replace with your domain)
# sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

echo "SSL setup script ready. Run with your domain when ready."
