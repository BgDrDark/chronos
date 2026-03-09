#!/bin/bash
# Generate self-signed SSL certificates for Chronos
# Run as: sudo bash generate-ssl.sh

set -e

SSL_DIR="/etc/nginx/ssl"
DOMAIN="dev.chronos.org"

echo "🔐 Generating self-signed SSL certificate..."

# Create directory if it doesn't exist
sudo mkdir -p "$SSL_DIR"

# Generate private key and certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
    -keyout "$SSL_DIR/server.key" \
    -out "$SSL_DIR/server.crt" \
    -subj "/C=BG/ST=Sofia/L=Sofia/O=Chronos/CN=$DOMAIN" \
    -addext "subjectAltName=DNS:$DOMAIN,DNS:localhost,IP:127.0.0.1"

# Set proper permissions
sudo chmod 600 "$SSL_DIR/server.key"
sudo chmod 644 "$SSL_DIR/server.crt"

echo "✅ SSL certificates generated successfully!"
echo ""
echo "📁 Certificate: $SSL_DIR/server.crt"
echo "🔑 Private key: $SSL_DIR/server.key"
echo ""
echo "⚠️  For production, replace with real certificates from:"
echo "   - Let's Encrypt (free)"
echo "   - Cloudflare Origin Certificates"
echo "   - Commercial CA (Sectigo, DigiCert, etc.)"
