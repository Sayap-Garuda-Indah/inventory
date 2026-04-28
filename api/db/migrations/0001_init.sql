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

