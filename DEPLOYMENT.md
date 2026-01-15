# Deployment Guide (Docker Desktop on Windows 10 with WSL2)

This guide deploys the Inventory app to a Docker host at `192.168.10.54` with three containers (MySQL, API, Frontend), restricts access to the local network, and sets up a virtual host at `sgi-inventory.local`.

## 1) Prepare the Windows 10 Server (Docker Desktop + WSL2)

1. Install WSL2 (PowerShell, Admin):
   ```powershell
   wsl --install
   wsl --set-default-version 2
   ```
2. Install Docker Desktop for Windows and enable:
   - Settings -> General -> "Use the WSL 2 based engine"
   - Settings -> Resources -> WSL Integration -> enable your distro
3. Ensure the server IP is `192.168.10.54`.

## 2) Clone the Repository

Use the WSL filesystem for best performance:

```bash
git clone <your-repo-url> /home/<wsl-user>/inventory
cd /home/<wsl-user>/inventory
```

## 3) Configure Environment Variables

Create a root `.env` file for Docker Compose:

```bash
cat > .env <<'EOF'
HOST_IP=192.168.10.54

MYSQL_ROOT_PASSWORD=change-me
DB_NAME=inventory
DB_USER=inv
DB_PASSWORD=change-me

JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

DEBUG=false
LOG_LEVEL=INFO

# Frontend uses the built-in Nginx reverse proxy
VITE_API_BASE_URL=/api

# Allow browser access from the virtual host
CORS_ORIGINS=["http://sgi-inventory.local"]

# Optional (if you use MSAL)
VITE_MSAL_CLIENT_ID=
VITE_MSAL_TENANT_ID=
VITE_MSAL_REDIRECT_URI=http://sgi-inventory.local
EOF
```

Notes:
- The MySQL schema is loaded from `api/db/schema.sql` on first boot.
- Set strong passwords before production.
- If Docker Desktop ignores the host binding, set `HOST_IP=0.0.0.0` and rely on Windows Firewall for access control.

## 4) Frontend Virtual Host (sgi-inventory.local)

The frontend container uses `front-end/nginx.conf` to:
- Serve the SPA.
- Proxy `/api` to the backend at `api:8000`.
- Declare `server_name sgi-inventory.local`.

If you need to change the host name, edit `front-end/nginx.conf` and rebuild.

## 5) Start the Containers

```bash
docker compose -f docker-compose.yaml up -d --build
```

This creates:
- `inventory-mysql` (MySQL 8)
- `inventory-api` (FastAPI, Python 3.12)
- `inventory-frontend` (Nginx serving the Vite build)

## 6) Restrict Access to the Local Network (Windows Firewall)

Use Windows Defender Firewall (PowerShell, Admin):

```powershell
New-NetFirewallRule -DisplayName "Inventory Frontend (LAN)" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 80 -RemoteAddress 192.168.10.0/24
New-NetFirewallRule -DisplayName "Inventory API (192.168.10.19)" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000 -RemoteAddress 192.168.10.19
New-NetFirewallRule -DisplayName "Inventory API (192.168.10.60)" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000 -RemoteAddress 192.168.10.60
New-NetFirewallRule -DisplayName "Inventory API (192.168.10.21)" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000 -RemoteAddress 192.168.10.21
```

## 7) Configure DNS or Hosts File

Add `sgi-inventory.local` so users do not need the IP address.

Option A (recommended): create a local DNS entry pointing `sgi-inventory.local` to `192.168.10.54`.

Option B (per-device hosts file):
- Linux/macOS: add to `/etc/hosts`
  ```
  192.168.10.54 sgi-inventory.local
  ```
- Windows: add to `C:\Windows\System32\drivers\etc\hosts`

## 8) Initialize the ADMIN User

1. Edit `api/scripts/create_admin.py` to set the desired email/password/name.
2. Run the script once:
   ```bash
   docker compose exec api python scripts/create_admin.py
   ```

If the user already exists, the script exits with a non-zero code, so only run it on first setup.

## 9) Verify

- Frontend: `http://sgi-inventory.local/`
- Backend health (from allowed IPs): `http://192.168.10.54:8000/health`

## 10) GitHub CI/CD Workflow

The workflow file is in `.github/workflows/ci-cd.yml`. It builds both images and deploys via SSH on every push to `main`.

### Required GitHub Secrets

```
DEPLOY_HOST=192.168.10.54
DEPLOY_USER=<ssh-user>
DEPLOY_SSH_KEY=<private-key>
DEPLOY_PORT=22
DEPLOY_PATH=/home/<wsl-user>/inventory

# Optional (for frontend build)
VITE_MSAL_CLIENT_ID=
VITE_MSAL_TENANT_ID=
VITE_MSAL_REDIRECT_URI=
```

### Server Prep for CI/CD (WSL SSH)

1. Install and enable OpenSSH Server inside WSL:
   ```bash
   sudo apt update
   sudo apt install -y openssh-server
   sudo service ssh start
   ```
2. Ensure `/home/<wsl-user>/inventory` is a git clone with the correct remote.
3. Create and keep the `.env` file on the server (the workflow does not overwrite it).
4. Add the deploy key to `/home/<wsl-user>/.ssh/authorized_keys`.

After pushing to `main`, the workflow will `git pull` and run:
`docker compose -f docker-compose.yaml up -d --build`.
