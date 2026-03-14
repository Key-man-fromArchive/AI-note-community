#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  echo ".env already exists"
else
  cp .env.example .env
  JWT_SECRET=$(openssl rand -base64 32 2>/dev/null || head -c 32 /dev/urandom | base64)
  OAUTH_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || openssl rand -base64 32)
  sed -i "s|^JWT_SECRET=.*|JWT_SECRET=${JWT_SECRET}|" .env
  sed -i "s|^OAUTH_ENCRYPTION_KEY=.*|OAUTH_ENCRYPTION_KEY=${OAUTH_KEY}|" .env
fi

docker compose up -d --build
docker compose exec -T backend alembic upgrade head

echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8001/docs"
