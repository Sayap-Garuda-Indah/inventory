# Deployment Guide (Docker Desktop on Windows 10 with WSL2)

This guide deploys the Inventory app to a Docker host at `192.168.10.64` with three containers (MySQL, API, Frontend), restricts access to the local network, and sets up a virtual host at `sgi-inventory.local`.

## 1) Prepare the Windows 10 Server (Docker Desktop + WSL2)

1. Install WSL2 (PowerShell, Admin):
   ```powershell
   wsl --install
   wsl --set-default-version 2
   ```
2. Install Docker Desktop for Windows and enable:
   - Settings -> General -> "Use the WSL 2 based engine"
   - Settings -> Resources -> WSL Integration -> enable your distro
3. Ensure the server IP is `192.168.10.64`.

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
HOST_IP=192.168.10.64

MYSQL_ROOT_PASSWORD=change-me
DB_NAME=inventory
DB_USER=inv
DB_PASSWORD=change-me

JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

DEBUG=false
LOG_LEVEL=INFO

ADMIN_EMAIL=admin@example.com
ADMIN_USERNAME=Administrator
ADMIN_PASSWORD=change-me

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
- For Docker Compose, only the root `.env` is required. Use `api/.env` and `front-end/.env` only for local (non-Docker) development.

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

Option A (recommended): create a local DNS entry pointing `sgi-inventory.local` to `192.168.10.64`.

Option B (per-device hosts file):
- Linux/macOS: add to `/etc/hosts`
  ```
  192.168.10.64 sgi-inventory.local
  ```
- Windows: add to `C:\Windows\System32\drivers\etc\hosts`

## 8) Initialize the ADMIN User

Admin user now dibuat otomatis saat container `api` start menggunakan variabel `ADMIN_EMAIL`, `ADMIN_USERNAME`, `ADMIN_PASSWORD` dari root `.env`.

Untuk re-run manual bila diperlukan:

```bash
docker compose exec api python scripts/create_admin.py
```

## 9) Verify

- Frontend: `http://sgi-inventory.local/`
- Backend health (from allowed IPs): `http://192.168.10.64:8000/health`

## 10) GitHub CI/CD Workflow

The workflow file is in `.github/workflows/ci-cd.yml`. It deploys via SSH on every push to `main`.

### Required GitHub Secrets

```
DEPLOY_HOST=192.168.10.64
DEPLOY_USER=devserver
DEPLOY_SSH_KEY=<private-key>
DEPLOY_PORT=22
DEPLOY_PATH=/home/devserver/inventory

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
4. Create a dedicated SSH key for GitHub Actions (in WSL):
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/inventory_ci -C "inventory-ci"
   ```
5. Add the public key to `/home/<wsl-user>/.ssh/authorized_keys`:
   ```bash
   cat ~/.ssh/inventory_ci.pub >> /home/<wsl-user>/.ssh/authorized_keys
   ```
6. Store the private key from `~/.ssh/inventory_ci` in the GitHub secret `DEPLOY_SSH_KEY`.

Note: the server still needs access to `git pull`. For private repos, configure a separate deploy key or a PAT on the server.

After pushing to `main`, the workflow will `git pull` and run:
`docker compose -f docker-compose.yaml up -d --build`.

### GitHub CI/CD Setup (Step-by-Step)

1. Push the repo to GitHub and ensure your default branch is `main`.
2. Add the workflow file to the repo:
   - Verify `.github/workflows/ci-cd.yml` exists in the repo.
3. Add required secrets:
   - GitHub -> Repo -> Settings -> Secrets and variables -> Actions -> New repository secret.
   - Add all keys listed in **Required GitHub Secrets** above.
4. Ensure the deploy host is reachable from GitHub Actions:
   - Open port `22` (or your `DEPLOY_PORT`) in Windows Firewall for GitHub Actions IPs, or allow `0.0.0.0/0` if you accept broader access.
   - Confirm WSL SSH is running and reachable: `ssh devserver@192.168.10.64 -p <port>`.
5. Trigger a deployment:
   - Push a commit to `main`, or
   - GitHub -> Actions -> Deploy -> Run workflow.
6. Verify on the server:
   - `docker compose ps`
   - `docker compose logs -f api`
