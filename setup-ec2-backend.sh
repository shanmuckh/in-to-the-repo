#!/bin/bash
# Initial EC2 setup script for backend deployment using pre-built images

set -e

echo "🚀 Into the Repo - Backend EC2 Setup"
echo "======================================="
echo ""

# Auto-detect EC2 Public IP
echo "Detecting EC2 Public IP..."
EC2_IP=$(curl -s http://checkip.amazonaws.com || curl -s ifconfig.me || echo "localhost")
echo "✓ Detected IP: ${EC2_IP}"
echo ""

# Prompt for credentials
echo "Please provide the following values:"
echo ""

read -p "Enter your GitHub Personal Access Token (with packages:read permission): " GITHUB_TOKEN
read -p "Enter your Gemini API Key: " GEMINI_API_KEY

# Generate secure passwords
echo ""
echo "Generating secure passwords..."
SECRET_KEY=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

echo "✓ Generated SECRET_KEY"
echo "✓ Generated DB_PASSWORD"
echo ""

# Create .env file
cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://repo_user:${DB_PASSWORD}@db:5432/into_the_repo
DB_USER=repo_user
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=into_the_repo
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_PORT=6379

# Authentication & Security
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# External APIs
GITHUB_TOKEN=${GITHUB_TOKEN}
GEMINI_API_KEY=${GEMINI_API_KEY}

# Application Configuration
BACKEND_PORT=8000
LOG_LEVEL=info
NODE_ENV=production
FRONTEND_HOST=https://into-the-repo.vercel.app
EOF

echo "✅ Created .env file"
echo ""

# Display configuration
echo "📋 Configuration Summary:"
echo "-------------------------"
echo "EC2 IP: ${EC2_IP}"
echo "DuckDNS Domain: into-the-repo.duckdns.org"
echo "Backend API (after SSL): https://into-the-repo.duckdns.org/docs"
echo "Database Password: ${DB_PASSWORD}"
echo "Secret Key: ${SECRET_KEY:0:20}..."
echo ""

# Save credentials
cat > ~/deployment-credentials.txt << EOF
Into the Repo - Deployment Credentials
======================================
Generated on: $(date)

EC2 Public IP: ${EC2_IP}
DuckDNS Domain: into-the-repo.duckdns.org
Database Password: ${DB_PASSWORD}
Secret Key: ${SECRET_KEY}

Backend API: https://into-the-repo.duckdns.org/docs

Deploy frontend on Vercel with:
NEXT_PUBLIC_HOST=https://into-the-repo.duckdns.org

IMPORTANT: Keep this file secure and delete after saving credentials elsewhere!
EOF

chmod 600 ~/deployment-credentials.txt
echo "💾 Credentials saved to: ~/deployment-credentials.txt"
echo "⚠️  IMPORTANT: Save these credentials securely, then delete the file!"
echo ""

# Ask to deploy
read -p "Start deployment now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Starting deployment..."
    echo ""
    
    # Use backend-only compose
    ln -sf docker-compose.backend.yml docker-compose.yml
    
    # Login to GitHub Container Registry
    echo "🔐 Logging into GitHub Container Registry..."
    echo "${GITHUB_TOKEN}" | docker login ghcr.io -u gourav1632 --password-stdin
    
    # Pull images (much faster than building!)
    echo "📦 Pulling Docker images from GitHub Container Registry..."
    docker compose pull
    
    # Start services
    echo "▶️  Starting services..."
    docker compose up -d
    
    echo ""
    echo "⏳ Waiting for services to start..."
    sleep 20
    
    # Show status
    echo ""
    echo "📊 Service Status:"
    docker compose ps
    
    echo ""
    echo "📋 Recent Logs:"
    docker compose logs --tail=30
    
    echo ""
    echo "✅ Deployment complete!"
    echo ""
    echo "🌐 Access your backend:"
    echo "   API Docs: https://into-the-repo.duckdns.org/docs"
    echo "   (Initial access: http://${EC2_IP}/docs - will redirect to HTTPS once SSL is active)"
    echo ""
    echo "⚠️  IMPORTANT: Set up DuckDNS domain pointing to ${EC2_IP}"
    echo "   1. Go to https://www.duckdns.org"
    echo "   2. Create subdomain: into-the-repo"
    echo "   3. Point to IP: ${EC2_IP}"
    echo "   4. Caddy will automatically obtain SSL certificate"
    echo ""
    echo "📝 View logs: docker compose logs -f"
    echo "🔄 Restart: docker compose restart"
    echo "🛑 Stop: docker compose down"
    echo ""
    echo "🎨 Deploy frontend on Vercel:"
    echo "   Set NEXT_PUBLIC_HOST=https://into-the-repo.duckdns.org"
else
    echo ""
    echo "Deployment skipped. To deploy manually later:"
    echo "  ln -sf docker-compose.backend.yml docker-compose.yml"
    echo "  echo 'YOUR_TOKEN' | docker login ghcr.io -u gourav1632 --password-stdin"
    echo "  docker compose pull"
    echo "  docker compose up -d"
fi

echo ""
echo "🎉 Setup complete!"