# Script to add /webhook location to nginx proxy config

# Create the webhook location config
cat > /tmp/webhook_location.conf << 'EOF'

  location /webhook {
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Scheme $scheme;
    proxy_set_header X-Forwarded-Proto  $scheme;
    proxy_set_header X-Forwarded-For    $remote_addr;
    proxy_set_header X-Real-IP           $remote_addr;

    proxy_pass       http://backend:14240;
    
    # CORS headers for webhook endpoints
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;
  }

EOF

echo "Webhook location config created. Copy it to nginx container and restart nginx."