# Inventory Manager (Internal Use) — Requirements, Design & Server Setup

> Stack: **FastAPI (Python)** backend • **React (Vite)** web app • **MySQL** DB • **JWT auth**

---

## 1) Scope & Key Goals

- Maintain a catalog of items with categories, units, optional owners, and active flags.
- Track issue requests and their line items with a simple approval/status workflow.
- Internal-use app with role-based access and low admin overhead.

## 2) Functional Requirements

### 2.1 Items, Categories, Units

- Items: create/read/update/delete (soft delete via active), unique SKU, required category + unit, optional owner_user_id, qrcode, min_stock, image_url.
- Categories: CRUD, list/search by name.
- Units: CRUD (Admin-only for mutations), list/search by name or symbol.

### 2.2 Issue Workflow

- Issues: create/update/delete; unique code; statuses DRAFT, APPROVED, ISSUED, CANCELLED.
- Approve: only when issue is DRAFT; set approved_by.
- Change status endpoint for administrative updates.
- Issue items: add/update/delete only when parent issue is DRAFT; prevent duplicate (issue_id, item_id); bulk add supported.
- Dashboard stats: status breakdown plus advanced averages/completion rate.

### 2.3 Users & Authentication

- Email/password login returns JWT access token.
- /auth/me returns current user profile.
- Users CRUD (Admin-only for create/update/delete); soft delete deactivates user; self-delete blocked.

### 2.4 Search & Pagination

- Pagination (page/page_size) on list endpoints.
- Search/filter: users (name/email), items (SKU/name), categories (name), units (name/symbol), issues (code/status + status_filter), issue items by issue_id or item_id.

### 2.5 Settings & System

- Single settings record: app_name, items_per_page, allow_negative_stock, low_stock_threshold, backup options, notifications.
- Admin-only: view/update settings, trigger manual backup, view system info.

## 3) Non-Functional Requirements

- Performance: typical request < 300ms under light load (1-20 users).
- Reliability: MySQL durability; manual/auto backup support via settings.
- Maintainability: typed schemas, service/repository layers, structured logging.
- Portability: local dev or Ubuntu 24.04 deployment.

---

## 5) Architecture Overview

```
React Web App (Vite)
    |
    | HTTPS + Bearer JWT
    v
FastAPI (uvicorn workers)
    |
    v
MySQL 8
```

- Auth flow (high level)
  1. User logs in with email/password via POST /auth/login and receives a JWT.
  2. Front-end stores token and sends Authorization: Bearer <token>.
  3. FastAPI validates JWT and enforces role checks per route.

---

## 6) Authentication & Authorization (Current)

- JWT access tokens signed by the API (HS256) with configurable expiry.
- Roles: ADMIN, STAFF, AUDITOR; role checks applied on mutation endpoints.
- Account state: inactive users cannot authenticate.

---

## 7) Data Model (ERD + DDL)

### 7.1 ERD (textual)

- users (id, name, email, password_hash, role, active, created_at)
- categories (id, name)
- units (id, name, symbol, multiplier)
- items (id, sku, name, category_id, unit_id, owner_user_id, qrcode, min_stock, image_url, active)
- issues (id, code, status, requested_by, approved_by, issued_at, note, updated_at)
- issue_items (id, issue_id, item_id, qty)
- settings (id=1, app_name, items_per_page, allow_negative_stock, auto_backup_enabled, backup_retention_days, low_stock_threshold, enable_notifications, updated_at, updated_by)

### 7.2 Minimal SQL DDL (MySQL 8)

```sql
CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('ADMIN','STAFF','AUDITOR') NOT NULL DEFAULT 'STAFF',
  active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE categories (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE units (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(40) NOT NULL UNIQUE,
  symbol VARCHAR(16) NOT NULL,
  multiplier DECIMAL(12,6) NOT NULL DEFAULT 1.0
) ENGINE=InnoDB;

CREATE TABLE items (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  sku VARCHAR(40) NOT NULL UNIQUE,
  name VARCHAR(160) NOT NULL,
  category_id BIGINT NOT NULL,
  unit_id BIGINT NOT NULL,
  owner_user_id BIGINT NULL,
  qrcode VARCHAR(64),
  min_stock DECIMAL(18,6) NOT NULL DEFAULT 0,
  image_url VARCHAR(255),
  active TINYINT(1) NOT NULL DEFAULT 1,
  CONSTRAINT fk_items_category FOREIGN KEY (category_id) REFERENCES categories(id),
  CONSTRAINT fk_items_unit FOREIGN KEY (unit_id) REFERENCES units(id),
  CONSTRAINT fk_items_owner FOREIGN KEY (owner_user_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE issues (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  code VARCHAR(40) NOT NULL UNIQUE,
  status ENUM('DRAFT','APPROVED','ISSUED','CANCELLED') NOT NULL DEFAULT 'DRAFT',
  requested_by BIGINT,
  approved_by BIGINT,
  issued_at DATETIME,
  note VARCHAR(255),
  updated_at DATETIME,
  CONSTRAINT fk_issue_req FOREIGN KEY (requested_by) REFERENCES users(id),
  CONSTRAINT fk_issue_app FOREIGN KEY (approved_by) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE issue_items (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  issue_id BIGINT NOT NULL,
  item_id BIGINT NOT NULL,
  qty DECIMAL(18,6) NOT NULL,
  CONSTRAINT fk_i_items_issue FOREIGN KEY (issue_id) REFERENCES issues(id),
  CONSTRAINT fk_i_items_item FOREIGN KEY (item_id) REFERENCES items(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS settings (
  id INT PRIMARY KEY DEFAULT 1,
  app_name VARCHAR(100) NOT NULL DEFAULT 'Inventory Management System',
  items_per_page INT NOT NULL DEFAULT 50,
  allow_negative_stock TINYINT(1) NOT NULL DEFAULT 0,
  auto_backup_enabled TINYINT(1) NOT NULL DEFAULT 1,
  backup_retention_days INT NOT NULL DEFAULT 30,
  low_stock_threshold INT NOT NULL DEFAULT 10,
  enable_notifications TINYINT(1) NOT NULL DEFAULT 1,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  updated_by BIGINT NULL,
  CONSTRAINT chk_id CHECK (id = 1),
  FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

INSERT INTO settings (id) VALUES (1)
ON DUPLICATE KEY UPDATE id=id;
```

---

## 8) API Design (current)

- Auth: `POST /auth/login`, `GET /auth/me`
- Users: `GET /users`, `GET /users/{id}`, `POST /users/register`, `POST /users/bulk-register`, `PUT /users/{id}`, `DELETE /users/{id}`
- Items: `GET /items`, `GET /items/{id}`, `POST /items`, `PUT /items/{id}`, `DELETE /items/{id}` (soft delete)
- Categories: `GET /categories`, `GET /categories/{id}`, `POST /categories`, `PUT /categories/{id}`, `DELETE /categories/{id}`
- Units: `GET /units`, `GET /units/{id}`, `POST /units`, `PUT /units/{id}`, `DELETE /units/{id}`
- Issues: `GET /issues`, `GET /issues/{id}`, `GET /issues/code/{code}`, `POST /issues`, `PUT /issues/{id}`, `DELETE /issues/{id}`, `PATCH /issues/{id}/approve`, `PATCH /issues/{id}/status`, `GET /issues/stats`, `GET /issues/advanced-stats`, `GET /issues/{id}/items`, `GET /issues/{id}/items-detailed`
- Issue items: `GET /issue-items`, `GET /issue-items/{id}`, `GET /issue-items/issue/{issue_id}`, `POST /issue-items`, `POST /issue-items/bulk`, `PUT /issue-items/{id}`, `DELETE /issue-items/{id}`
- Settings: `GET /settings`, `PUT /settings`, `POST /settings/backup`, `GET /settings/system-info`
- Health: `GET /health`

**AuthN/Z**

- `Authorization: Bearer <access_token>` required for protected endpoints.
- Role guard: Admin required for user management, unit mutations, settings, and delete operations for items, categories, and issues; staff can manage items, categories, issues, and issue items.

---

## 9) Ubuntu 24.04 Server Setup (LAN‑only)

> Assumes fresh VM and sudo access; replace variables in ALL‑CAPS.

### 9.1 Base packages & firewall

```bash
sudo apt update && sudo apt -y upgrade
sudo apt -y install build-essential curl git ufw unzip

# Firewall: allow only LAN (replace 192.168.10.0/24)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 192.168.10.0/24 to any port 22 proto tcp
sudo ufw allow from 192.168.10.0/24 to any port 80,443 proto tcp
sudo ufw enable
sudo ufw status
```

### 9.2 Install Python & virtual env (system Python 3.12 is default on 24.04)

```bash
python3 --version  # expect 3.12.x
sudo apt -y install python3-venv python3-dev
# optional: faster installer
pipx ensurepath || true; python3 -m pip install --user pipx && ~/.local/bin/pipx ensurepath
```

### 9.3 FastAPI app skeleton

```bash
sudo mkdir -p /opt/inventory/api && sudo chown -R $USER:$USER /opt/inventory
cd /opt/inventory/api
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn[standard] python-jose[cryptography] httpx pydantic-settings mysqlclient orjson

cat > app.py <<'PY'
from fastapi import FastAPI
app = FastAPI(title="Inventory API")
@app.get("/health")
def health():
    return {"ok": True}
PY
```

### 9.4 MySQL 8 install & secure

```bash
sudo apt -y install mysql-server
sudo systemctl enable --now mysql
sudo mysql_secure_installation  # set root password, remove test DB, etc.

# Create DB & user
sudo mysql <<'SQL'
CREATE DATABASE inventory CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER 'inv_user'@'%' IDENTIFIED BY 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON inventory.* TO 'inv_user'@'%';
FLUSH PRIVILEGES;
SQL

# Bind only to LAN interface (optional hardening)
sudo sed -i 's/^bind-address.*/bind-address = 192.168.10.5/' /etc/mysql/mysql.conf.d/mysqld.cnf
sudo systemctl restart mysql
```

### 9.5 Nginx reverse proxy (LAN only)

```bash
sudo apt -y install nginx
# Allow only LAN subnet
sudo tee /etc/nginx/sites-available/inventory.conf >/dev/null <<'NGX'
server {
  listen 80;
  server_name inventory.lan;

  # deny non-LAN traffic
  allow 192.168.10.0/24;
  deny all;

  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
NGX
sudo ln -s /etc/nginx/sites-available/inventory.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 9.6 systemd service for FastAPI (uvicorn)

```bash
sudo tee /etc/systemd/system/inventory-api.service >/dev/null <<'UNIT'
[Unit]
Description=Inventory FastAPI Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/inventory/api
Environment="PATH=/opt/inventory/api/.venv/bin"
ExecStart=/opt/inventory/api/.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

sudo chown -R www-data:www-data /opt/inventory
sudo systemctl daemon-reload
sudo systemctl enable --now inventory-api
systemctl status inventory-api
```

> **Why 127.0.0.1?** The API listens only on localhost; Nginx handles LAN traffic and blocks non‑LAN IPs.

### 9.7 Environment variables

Create `/opt/inventory/api/.env` (use `pydantic-settings`):

```
DB_URI=mysql+mysqlclient://inv_user:STRONG_PASSWORD_HERE@192.168.10.5/inventory
OIDC_TENANT_ID=...
OIDC_AUDIENCE=api://inventory.local
OIDC_ISSUER=https://login.microsoftonline.com/<TENANT_ID>/v2.0
JWKS_URL=https://login.microsoftonline.com/<TENANT_ID>/discovery/v2.0/keys
```

---

## 10) React Native App Notes

- Use \`\` for Entra ID login (PKCE).
- After sign‑in, store access token securely (Keychain/Keystore) and send it as `Authorization: Bearer` header.
- API base URL: `http://inventory.lan/` (ensure device can resolve DNS or host file; or use IP).
- QR Code: add `react-native-camera`/`vision-camera` plugin for scanning (optional feature).

**Minimal request**

```js
const res = await fetch('http://inventory.lan/items', {
  headers: { Authorization: `Bearer ${accessToken}` }
});
```

---

## 11) Token Validation (FastAPI)

- Fetch Entra **OpenID configuration** & **JWKS** on startup and cache keys.
- Validate: signature, `iss`, `aud`, `exp`, and presence of `oid` claim → map to `users.m365_oid`.
- On first login, auto‑provision a `users` row with default role if email domain matches your org.

---

## 12) Backups & Monitoring

- **MySQL**: nightly `mysqldump` to local disk + rsync to NAS.
- **Logs**: `journalctl -u inventory-api -f` for live API logs; Nginx access/error logs.
- **Health**: `/health` endpoint; optional `fail2ban` for Nginx.

---

## 13) Phased Implementation Plan

1. Stand up server (Sections 9.1–9.6) and create DB with DDL (7.2).
2. Implement auth validation & `/me`, then master data (items, categories, locations, units).
3. Implement stock IN/OUT/ADJ flows + consistent stock update service.
4. Add PO/Issue modules; then reporting & CSV export.
5. Add qrcode scanning and attachments if needed.

---

## 14) Nice‑to‑Haves (later)

- Role‑based UI in RN, offline queue for transactions if Wi‑Fi drops.
- Read replicas (MySQL) if reporting grows.
- WireGuard site‑to‑site to access API from remote offices, still private.

---

### Appendix A — Sample Stock Update (pseudo)

```sql
-- inside one DB transaction
INSERT INTO stock_tx(item_id,location_id,tx_type,qty,ref,note,user_id)
VALUES(:item_id,:loc_id,'IN',:qty,:ref,:note,:user_id);

INSERT INTO stock_levels(item_id,location_id,qty_on_hand)
VALUES(:item_id,:loc_id,:qty)
ON DUPLICATE KEY UPDATE qty_on_hand = qty_on_hand + VALUES(qty_on_hand);
```

### Appendix B — Simple RBAC (FastAPI dependency pseudo)

```python
from fastapi import Depends, HTTPException

def require_role(*roles):
    def wrapper(user=Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="forbidden")
        return user
    return wrapper
```

---

## How to run the project in development mode

```
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Directory Structure

```
/opt/inventory/api/
├─ app/
│  ├─ main.py                     # FastAPI app factory + routers mounting
│  ├─ dependencies.py             # DI helpers (db session, current_user, RBAC)
│  ├─ middleware.py               # logging, CORS (LAN only), request id
│  ├─ routers/
│  │  ├─ auth.py                  # /auth endpoints (token debug, /me)
│  │  ├─ items.py                 # CRUD + search
│  │  ├─ stock.py                 # in/out/adjust/transfer ops
│  │  ├─ master.py                # categories, units, locations
│  │  ├─ po.py                    # purchase orders (with supplier_name)
│  │  └─ reports.py               # CSV exports, summaries
│  └─ __init__.py
│
├─ core/
│  ├─ config.py                   # Pydantic Settings (DB_URI, OIDC, etc.)
│  ├─ logging.py                  # structlog / std logging config
│  ├─ security/
│  │  ├─ oidc.py                  # Entra OIDC validation (issuer, aud, JWKS cache)
│  │  └─ rbac.py                  # role checks, decorators
│  └─ __init__.py
│
├─ db/
│  ├─ session.py                  # session generator for DI
│  ├─ models/                     # SQL models
│  │  ├─ user.py
│  │  ├─ item.py                  # + owner_user_id FK (nullable)
│  │  ├─ category.py
│  │  ├─ unit.py
│  │  ├─ location.py
│  │  ├─ stock.py                 # stock_levels, stock_tx
│  │  ├─ purchase_order.py        # supplier_name, status, dates
│  │  └─ audit.py
│  ├─ repositories/               # DB access (no business rules)
│  │  ├─ user_repo.py
│  │  ├─ item_repo.py
│  │  ├─ stock_repo.py
│  │  ├─ po_repo.py
│  │  └─ ...
│  └─ __init__.py
│
├─ domain/                        # Business logic (pure services)
│  ├─ services/
│  │  ├─ stock_service.py         # single source of truth for qty updates (+tx)
│  │  ├─ item_service.py
│  │  ├─ po_service.py
│  │  └─ report_service.py
│  ├─ rules.py                    # invariants (e.g., stock integrity)
│  └─ __init__.py
│
├─ schemas/                       # Pydantic request/response models
│  ├─ auth.py
│  ├─ items.py
│  ├─ stock.py
│  ├─ master.py
│  ├─ po.py
│  └─ common.py
│
├─ migrations/                    # Alembic (autogenerated + hand-tuned)
│  ├─ versions/
│  └─ env.py
│
├─ tests/
│  ├─ conftest.py                 # test DB, fixtures
│  ├─ test_auth.py
│  ├─ test_items.py
│  ├─ test_stock.py
│  └─ ...
│
├─ scripts/                       # admin/ops helpers
│  ├─ seed_data.py
│  └─ backup.sh
│
├─ .env.example                   # template env vars
├─ alembic.ini
├─ pyproject.toml                 # or requirements.txt
└─ README.md
```

---

## Properly Configure Your API in Entra ID

Follow these steps to expose your API correctly:

### Step 1: Configure the API App Registration

Go to Azure Portal → Entra ID → App registrations

Find your API app (the one with ID 6d7e2d54-e45e-49f1-9f4e-919ce695a15b)

Click on Expose an API

Set the Application ID URI:

- Click Add next to "Application ID URI"
- Use: api://6d7e2d54-e45e-49f1-9f4e-919ce695a15b (should match your client ID)
- Click Save

Add a scope:

- Click + Add a scope
- Scope name: access_as_user
- Who can consent: Admins and users
- Admin consent display name: Access Inventory API
- Admin consent description: Allows the app to access the Inventory API on behalf of the signed-in user
- User consent display name: Access Inventory API
- User consent description: Allows the app to access the Inventory API on your behalf
- State: Enabled
- Click Add scope

### Step 2: Configure the Web App Registration

Go to Azure Portal → Entra ID → App registrations

Find your Web App (the one you're using for the front-end)

Go to API permissions

- Click + Add a permission
- Select My APIs tab
- Find your API app (6d7e2d54-e45e-49f1-9f4e-919ce695a15b)
- Select Delegated permissions
- Check access_as_user
- Click Add permissions
- Click Grant admin consent (if you're an admin)

### Step 3: Update Authentication Settings

In your Web App registration:

Go to Authentication

Under Platform configurations, add Single-page application:

- Redirect URI: http://localhost:5173

Under Implicit grant and hybrid flows, enable:

- ✅ Access tokens
- ✅ ID tokens