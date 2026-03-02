-- VaultPass CTF - Ma'lumotlar bazasi sxemasi
-- Musobaqa: chconf.uz | Flag formati: CHC{...}

CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(100) UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    secondary_email VARCHAR(255) DEFAULT NULL,
    is_admin        BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tokens (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       VARCHAR(128) NOT NULL UNIQUE,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMP NOT NULL DEFAULT (NOW() + INTERVAL '2 hours')
);

CREATE TABLE vault_entries (
    id             SERIAL PRIMARY KEY,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    site_name      VARCHAR(255) NOT NULL,
    site_url       VARCHAR(500),
    vault_username VARCHAR(255),
    vault_password TEXT,
    notes          TEXT,
    created_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE app_config (
    config_key   VARCHAR(100) PRIMARY KEY,
    config_value TEXT NOT NULL,
    description  TEXT
);

-- -----------------------------------------------------------------------
-- Foydalanuvchilar
-- Parollar murakkab tasodifiy qatorlar (bcrypt cost 12) — buzib bo'lmaydi
-- -----------------------------------------------------------------------
INSERT INTO users (username, email, password_hash, is_admin) VALUES (
    'aziz',
    'aziz@chconf.uz',
    '$2b$12$Hgzt1fqUtfcUhmXFa1Oq..LvUynTBn9EHJBXK0KnqtRjmHDXRSDOK',
    TRUE
);

INSERT INTO users (username, email, password_hash) VALUES (
    'jasur',
    'jasur@chconf.uz',
    '$2b$12$Ww0XlSGJwxcDMgC7ZMTNXe2atERau92PL.oNY3xMlbFWgt.YxOxxm'
);

INSERT INTO users (username, email, password_hash) VALUES (
    'nodira',
    'nodira@chconf.uz',
    '$2b$12$lH78XyjqslNoqDFmxXV32e.WJ0LoXz0n1Y4PJhF5mQnowggEk8/Wa'
);

-- -----------------------------------------------------------------------
-- Admin seyf yozuvlari (hisob egallab olingandan so'ng ko'rinadi)
-- -----------------------------------------------------------------------
INSERT INTO vault_entries (user_id, site_name, site_url, vault_username, vault_password, notes)
SELECT id,
       'GitHub Enterprise',
       'https://github.com/chconf-uz-internal',
       'aziz@chconf.uz',
       '[SHIFRLANGAN]gh_pat_x7Kq9mZnP8sQ1v',
       'Ichki GitHub — ishlab chiqarish repo'
FROM users WHERE username = 'aziz';

INSERT INTO vault_entries (user_id, site_name, site_url, vault_username, vault_password, notes)
SELECT id,
       'Yandex Cloud Console',
       'https://console.cloud.yandex.uz',
       'aziz.admin@chconf.uz',
       '[SHIFRLANGAN]yc_secret_AKIAIOSFODNN7',
       'Ishlab chiqarish serveri — ehtiyotkorlik bilan'
FROM users WHERE username = 'aziz';

INSERT INTO vault_entries (user_id, site_name, site_url, vault_username, vault_password, notes)
SELECT id,
       'Ichki Admin Panel',
       'http://admin.internal.chconf.uz',
       'superadmin',
       '[SHIFRLANGAN]adm1n_ichki_s3cr3t_2024',
       'Ichki admin panel — cheklangan kirish'
FROM users WHERE username = 'aziz';

INSERT INTO vault_entries (user_id, site_name, site_url, vault_username, vault_password, notes)
SELECT id,
       'PostgreSQL Ishlab Chiqarish DB',
       'postgresql://db.internal.chconf.uz:5432',
       'db_admin',
       '[SHIFRLANGAN]pg_pr0d_s3cur3_2024!',
       'Ishlab chiqarish bazasi — ULASHMANG'
FROM users WHERE username = 'aziz';

-- -----------------------------------------------------------------------
-- Ilova konfiguratsiyasi
-- Eslatma: import shifrlash kalitlari endi /web.ini faylida saqlanadi
-- (error-based SQLi + pg_read_file() orqali o'qiladi)
-- -----------------------------------------------------------------------
INSERT INTO app_config (config_key, config_value, description) VALUES (
    'app_version',
    '2.4.1',
    'Ilova versiyasi'
);

INSERT INTO app_config (config_key, config_value, description) VALUES (
    'max_vault_entries',
    '500',
    'Foydalanuvchi boshiga maksimal seyf yozuvlari'
);
