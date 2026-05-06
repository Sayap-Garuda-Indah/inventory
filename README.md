# Inventory Manager (Internal Use) — Requirements, Design & Server Setup

> Stack: **FastAPI (Python)** backend • **React (Vite)** web app • **MySQL** DB • **JWT auth**

---

## 1) Scope & Key Goals

- Maintain a catalog of items with categories, units, optional owners, and active flags.
- Track issue requests and their line items with a simple approval/status workflow.
- Internal-use app with role-based access and low admin overhead.

## 2) Functional Requirements

### 2.1 Items, Categories, Units

- Items: create/read/update/delete (soft delete via active), unique item_code, required category + unit, optional owner_user_id, serial_number, min_stock, description, image_url.
- Categories: CRUD, list/search by name.
- Units: CRUD (Admin-only for mutations), list/search by name or symbol.

### 2.2 Locations & Stock

- Locations: list/search by name or code; location records can be active/inactive.
- Stock levels: list by item/location with search and pagination.
- Stock transactions: create/update/delete; types IN/OUT/ADJ/XFER; affect stock levels.

### 2.3 Issue Workflow

- Issues: create/update/delete; unique code; statuses DRAFT, APPROVED, ISSUED, CANCELLED.
- Approve: only when issue is DRAFT; set approved_by.
- Change status endpoint for administrative updates.
- Issue items: add/update/delete only when parent issue is DRAFT; prevent duplicate (issue_id, item_id); bulk add supported.
- Dashboard stats: status breakdown plus advanced averages/completion rate.

### 2.4 Users & Authentication

- Email/password login returns JWT access token.
- /auth/me returns current user profile.
- Users CRUD (Admin-only for create/update/delete); soft delete deactivates user; self-delete blocked.

### 2.5 Search & Pagination

- Pagination (page/page_size) on list endpoints.
- Search/filter: users (name/email), items (item_code/name/description), categories (name), units (name/symbol), locations (name/code), issues (code/status + status_filter), issue items by issue_id or item_id, transactions (item/location/ref/note), stock levels (item/location).

### 2.6 Audit & Settings

- Audit sessions: create/list/get/close, scan items, reconcile results, capture notes.
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
- locations (id, name, code, active)
- items (id, item_code, serial_number, name, category_id, unit_id, owner_user_id, min_stock, description, image_url, active)
- stock_levels (id, item_id, location_id, qty_on_hand, updated_at)
- stock_tx (id, item_id, location_id, tx_type, qty, ref, note, tx_at, user_id)
- issues (id, code, status, requested_by, approved_by, issued_at, note, updated_at)
- issue_items (id, issue_id, item_id, qty)
- attachments (id, entity_type, entity_id, file_url, note)
- audit_log (id, actor_user_id, action, entity_type, entity_id, session_id, ip_address, user_agent, payload_json, created_at)
- settings (id=1, app_name, items_per_page, allow_negative_stock, auto_backup_enabled, backup_retention_days, low_stock_threshold, enable_notifications, updated_at, updated_by)
- audit_sessions (id, location_id, status, started_at, started_by, closed_at, closed_by, note, scanned_count, expected_count, missing_count, unexpected_count, unknown_count)
- audit_scans (id, session_id, scanned_at, scanned_by, scanned_code, item_id, location_id, result, note)

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

CREATE TABLE locations (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(80) NOT NULL,
  code VARCHAR(24) NOT NULL UNIQUE,
  active TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB;

CREATE TABLE categories (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE units (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(40) NOT NULL UNIQUE,
  symbol VARCHAR(16) NOT NULL,
  multiplier DECIMAL(12,6) NOT NULL DEFAULT 1.0 -- for conversion if needed
) ENGINE=InnoDB;

CREATE TABLE items (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  item_code VARCHAR(20) NOT NULL UNIQUE,
  serial_number VARCHAR(30) UNIQUE,
  name VARCHAR(160) NOT NULL,
  category_id BIGINT NOT NULL,
  unit_id BIGINT NOT NULL,
  owner_user_id BIGINT NULL,
  min_stock DECIMAL(18,6) NOT NULL DEFAULT 0,
  description VARCHAR(500),
  image_url VARCHAR(255),
  active TINYINT(1) NOT NULL DEFAULT 1,
  CONSTRAINT fk_items_category FOREIGN KEY (category_id) REFERENCES categories(id),
  CONSTRAINT fk_items_unit FOREIGN KEY (unit_id) REFERENCES units(id),
  CONSTRAINT fk_items_owner FOREIGN KEY (owner_user_id) REFERENCES users(id)
) ENGINE=InnoDB;

-- ALTER TABLE items
--   ADD COLUMN owner_user_id BIGINT NOT NULL AFTER unit_id,
--   ADD CONSTRAINT fk_items_owner FOREIGN KEY (owner_user_id) REFERENCES users(id);

CREATE TABLE stock_levels (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  item_id BIGINT NOT NULL,
  location_id BIGINT NOT NULL,
  qty_on_hand DECIMAL(18,6) NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_item_location (item_id, location_id), -- ensures one row per item/location
  CONSTRAINT fk_sl_item FOREIGN KEY (item_id) REFERENCES items(id),
  CONSTRAINT fk_sl_loc FOREIGN KEY (location_id) REFERENCES locations(id)
) ENGINE=InnoDB;

CREATE TABLE stock_tx (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  item_id BIGINT NOT NULL,
  location_id BIGINT NOT NULL,
  tx_type ENUM('IN','OUT','ADJ','XFER') NOT NULL,
  qty DECIMAL(18,6) NOT NULL,
  ref VARCHAR(80),
  note VARCHAR(255),
  tx_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  user_id BIGINT NOT NULL,
  CONSTRAINT fk_tx_item FOREIGN KEY (item_id) REFERENCES items(id),
  CONSTRAINT fk_tx_loc FOREIGN KEY (location_id) REFERENCES locations(id),
  CONSTRAINT fk_tx_user FOREIGN KEY (user_id) REFERENCES users(id)
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

CREATE TABLE attachments (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  entity_type VARCHAR(40) NOT NULL, -- e.g., 'ITEM','PO','ISSUE'
  entity_id BIGINT NOT NULL,
  file_url VARCHAR(255) NOT NULL,
  note VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE audit_log (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  actor_user_id BIGINT NOT NULL,
  action ENUM('AUDIT_SESSION_CREATE', 'AUDIT_SCAN', 'AUDIT_SESSION_CLOSE') NOT NULL,
  entity_type VARCHAR(40) NOT NULL,
  entity_id BIGINT,
  session_id BIGINT NULL,
  ip_address VARCHAR(45) NULL,
  user_agent VARCHAR(255) NULL,
  payload_json JSON,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_audit_entity (entity_type, entity_id),
  INDEX idx_audit_session (session_id),
  CONSTRAINT fk_audit_user FOREIGN KEY (actor_user_id) REFERENCES users(id)
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

-- Insert default settings
INSERT INTO settings (id) VALUES (1)
ON DUPLICATE KEY UPDATE id=id;

CREATE TABLE audit_sessions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  location_id BIGINT NOT NULL,
  status ENUM('OPEN','CLOSED','CANCELLED') NOT NULL DEFAULT 'OPEN',
  started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  started_by BIGINT NOT NULL,
  closed_at TIMESTAMP NULL,
  closed_by BIGINT NULL,
  note VARCHAR(255),

  -- summary fields (optional but useful for fast reporting)
  scanned_count INT NOT NULL DEFAULT 0,
  expected_count INT NOT NULL DEFAULT 0,
  missing_count INT NOT NULL DEFAULT 0,
  unexpected_count INT NOT NULL DEFAULT 0,
  unknown_count INT NOT NULL DEFAULT 0,

  CONSTRAINT fk_audit_sess_loc FOREIGN KEY (location_id) REFERENCES locations(id),
  CONSTRAINT fk_audit_sess_started_by FOREIGN KEY (started_by) REFERENCES users(id),
  CONSTRAINT fk_audit_sess_closed_by FOREIGN KEY (closed_by) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE INDEX idx_audit_sessions_location_status ON audit_sessions(location_id, status);

CREATE TABLE audit_scans (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  session_id BIGINT NOT NULL,
  scanned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  scanned_by BIGINT NOT NULL,

  -- QR payload not stored
  scanned_code VARCHAR(64) NULL,

  -- resolved item if found
  item_id BIGINT NULL,

  -- audit context
  location_id BIGINT NOT NULL,

  result ENUM('FOUND','UNKNOWN','INACTIVE','WRONG_LOCATION','DUPLICATE','MISSING') NOT NULL DEFAULT 'FOUND',
  note TEXT,

  CONSTRAINT fk_audit_scan_session FOREIGN KEY (session_id) REFERENCES audit_sessions(id) ON DELETE CASCADE,
  CONSTRAINT fk_audit_scan_user FOREIGN KEY (scanned_by) REFERENCES users(id),
  CONSTRAINT fk_audit_scan_item FOREIGN KEY (item_id) REFERENCES items(id),
  CONSTRAINT fk_audit_scan_loc FOREIGN KEY (location_id) REFERENCES locations(id)
) ENGINE=InnoDB;

CREATE INDEX idx_audit_scans_session ON audit_scans(session_id);
CREATE INDEX idx_audit_scans_item ON audit_scans(item_id);

```

---

## Database migrations

- SQL migrations live in `api/db/migrations/` (e.g. `0001_init.sql`).
- Apply pending migrations: `cd api && python scripts/migrate.py upgrade`
- In Docker deployments, migrations run automatically on API container start (`api/docker-entrypoint.sh`).
- Legacy: `api/db/schema.sql` is kept as a baseline reference only.

## 8) API Design (current)

- Auth: `POST /auth/login`, `GET /auth/me`
- Users: `GET /users`, `GET /users/{id}`, `POST /users/register`, `POST /users/bulk-register`, `PUT /users/{id}`, `DELETE /users/{id}`, `PATCH /users/{id}/activate`
- Items: `GET /items`, `GET /items/{id}`, `POST /items`, `PUT /items/{id}`, `DELETE /items/{id}` (soft delete)
- Categories: `GET /categories`, `GET /categories/{id}`, `POST /categories`, `PUT /categories/{id}`, `DELETE /categories/{id}`
- Units: `GET /units`, `GET /units/{id}`, `POST /units`, `PUT /units/{id}`, `DELETE /units/{id}`
- Locations: `GET /locations`, `GET /locations/{id}`
- Issues: `GET /issues`, `GET /issues/{id}`, `GET /issues/code/{code}`, `POST /issues`, `PUT /issues/{id}`, `DELETE /issues/{id}`, `PATCH /issues/{id}/approve`, `PATCH /issues/{id}/status`, `GET /issues/stats`, `GET /issues/advanced-stats`, `GET /issues/{id}/items`, `GET /issues/{id}/items-detailed`
- Issue items: `GET /issue-items`, `GET /issue-items/{id}`, `GET /issue-items/issue/{issue_id}`, `POST /issue-items`, `POST /issue-items/bulk`, `PUT /issue-items/{id}`, `DELETE /issue-items/{id}`
- Transactions: `GET /transactions`, `GET /transactions/{id}`, `POST /transactions`, `PUT /transactions/{id}`, `DELETE /transactions/{id}`, `GET /transactions/stock-levels`
- Audit: `POST /audit/sessions`, `GET /audit/sessions`, `GET /audit/sessions/{id}`, `POST /audit/sessions/{id}/scans`, `GET /audit/sessions/{id}/scans`, `GET /audit/sessions/{id}/reconciliation`, `POST /audit/sessions/{id}/notes`, `POST /audit/sessions/{id}/close`
- Settings: `GET /settings`, `PUT /settings`, `POST /settings/backup`, `GET /settings/system-info`
- Health: `GET /health`

**AuthN/Z**

- `Authorization: Bearer <access_token>` required for protected endpoints.
- Role guard: Admin required for user management, unit mutations, settings, and delete operations for items, categories, and issues; staff can manage items, categories, issues, and issue items.

---

Coding scheme:
- Issue coding scheme


- Item coding scheme:
  ```
  PREFIX-XXXX-XXXX
  ```
  - PREFIX: SGI / FI
  - xxxx: sequence number, zero-padded to 4 digits (e.g., 0001, 0002, ...)
  - XXXX: 2-4 letter code representing the item category.

- Item category coding scheme:
  ```
  CAT-XXX
  ```
  - CAT: fixed prefix
  - XXX: sequence number, zero-padded to 3 digits (e.g., 001, 002, ...)

- Location coding scheme:
  ```
  LOC-XXX
  ```
  - LOC: fixed prefix
  - XXX: sequence number, zero-padded to 3 digits (e.g., 001, 002, ...)