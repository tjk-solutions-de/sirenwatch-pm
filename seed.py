#!/usr/bin/env python3
"""
SirenWatch PM — Seed-Script
Befüllt die Datenbank mit allen Projekten und Aufgaben aus dem Plattform-Konzept.
Verwendung: python3 seed.py [--db /pfad/zur/pm.db]
"""
import argparse
import sqlite3
import time
from pathlib import Path

PROJECTS = [
    {"name": "Infrastructure & DevOps",    "color": "#2563eb", "description": "Monorepo, Docker Compose, Traefik, CI/CD, Keycloak, Valkey, NATS, PostgreSQL HA, Observability, Kubernetes, Secrets"},
    {"name": "Datenbank",                  "color": "#16a34a", "description": "Schema, Indexes, TimescaleDB, Alembic Migrationen, Backup & Recovery"},
    {"name": "Backend — Ingest API",        "color": "#dc2626", "description": "Drop-in Kompatibilität mit bestehenden Bridges, Token-Auth, NATS Publish"},
    {"name": "Backend — Core API",          "color": "#9333ea", "description": "REST Endpoints: Tenants, Devices, Alarms, Users, Audit, Decoder, Notifications, Tokens, WebSocket"},
    {"name": "Backend — Alert Service",     "color": "#d97706", "description": "NATS Consumer, Regelengine, Apprise-Notifications, Eskalationsketten"},
    {"name": "Frontend",                    "color": "#0891b2", "description": "Next.js 15, Karte, Status Grid/NOC, Bundesland-Dashboard, Alarm Center, Admin Panel"},
    {"name": "SDS Decoder",                 "color": "#65a30d", "description": "Konfigurierbare Decoder-Profile, DB-gespeichert, UI-Editor, Import/Export"},
    {"name": "Security & Compliance",       "color": "#b91c1c", "description": "MFA, SAML, Audit-Log, DSGVO, OWASP, BSI IT-Grundschutz"},
    {"name": "Dokumentation",               "color": "#7c3aed", "description": "API-Docs, Deployment-Guides, Benutzer-Handbuch, Admin-Handbuch, Runbooks"},
]

TASKS = {
    "Infrastructure & DevOps": [
        # Monorepo & Projektstruktur
        ("Monorepo-Struktur anlegen: frontend/, backend/api/, backend/ingest/, backend/alert/, backend/admin/, infra/docker/, infra/k8s/, infra/helm/, docs/, scripts/", "high"),
        (".gitignore mit Ausschlüssen für alle Sprachen (Python, Node, Docker, IDE-Dateien)", "normal"),
        ("pyproject.toml je Backend-Service (Ruff, Black, pytest-Konfiguration)", "normal"),
        ("package.json für Frontend (Next.js 15, shadcn/ui, TanStack Query)", "normal"),
        ("Pre-commit Hooks: Ruff (lint + format), ESLint, Prettier", "normal"),
        # Docker Compose
        ("docker-compose.dev.yml mit allen Services (Traefik, Frontend, API, Ingest, Alert, Admin, PostgreSQL+TimescaleDB, Valkey, NATS, Keycloak, Prometheus, Grafana, Loki)", "high"),
        ("docker-compose.prod.yml (HA-fähig, Secrets via Docker Secrets)", "high"),
        (".env.example für alle erforderlichen Umgebungsvariablen", "normal"),
        ("Volume-Definitionen für persistente Daten (PostgreSQL, Valkey, NATS)", "normal"),
        ("Health-Check-Definitionen für alle Container", "normal"),
        ("Named Networks: frontend-net, backend-net, db-net, monitoring-net", "low"),
        # Traefik
        ("Traefik v3 konfigurieren: automatisches TLS (Let's Encrypt ACME), HTTP → HTTPS Redirect", "high"),
        ("Routing-Regeln: /ingest/* → Ingest, /api/* → API, /admin/* → Admin, /auth/* → Keycloak, * → Frontend", "high"),
        ("Rate Limiting Middleware: global + per-IP-Limit konfigurieren", "normal"),
        ("Security Headers Middleware: HSTS, X-Frame-Options, X-Content-Type-Options, CSP", "normal"),
        ("BasicAuth oder ForwardAuth für Traefik Dashboard absichern", "normal"),
        ("accessLog aktivieren (für Audit/SIEM)", "low"),
        ("Health-Check-Endpoint: GET /ping", "low"),
        # CI/CD
        ("lint.yml: Ruff (Python), ESLint (TypeScript), markdownlint — auf allen PRs", "normal"),
        ("test.yml: pytest mit Coverage-Report (>= 80 %), vitest für Frontend", "high"),
        ("build.yml: Docker-Images bauen (multi-platform: amd64, arm64), in Registry pushen", "high"),
        ("deploy-staging.yml: Automatisches Deployment nach Staging bei Push auf main", "normal"),
        ("deploy-prod.yml: Manuell getriggertes Production Deployment mit Approval-Step", "high"),
        ("security-scan.yml: Trivy Container-Scan + Semgrep SAST — blockiert bei kritischen Findings", "high"),
        ("Dependabot aktivieren (Python, npm, GitHub Actions, Docker)", "normal"),
        ("Branch-Protection Rules: main geschützt, PRs erfordern grüne Checks + Review", "normal"),
        # Container Registry
        ("Container Registry einrichten (GitHub Packages oder Gitea Registry)", "normal"),
        ("Image-Tags: latest (main), <version> (releases), <commit-sha> (alle Builds)", "normal"),
        ("Image-Pruning: Alte Images nach 30 Tagen automatisch löschen", "low"),
        # Keycloak
        ("Keycloak 24.x Realm 'sirenwatch' anlegen", "high"),
        ("OIDC Clients anlegen: sirenwatch-frontend (public, PKCE), sirenwatch-api (confidential)", "high"),
        ("Realm Roles anlegen: platform_admin, country_admin, state_admin, district_admin, municipality_operator, bdbos_viewer, asbb_viewer, auditor, viewer", "high"),
        ("Token Claims konfigurieren: tenant_id, roles im Access Token", "high"),
        ("Password Policy: Mindestens 12 Zeichen, Komplexitätsregeln", "normal"),
        ("Session-Timeouts: Access Token 15 min, Refresh Token 12h, SSO Session 30 min Inaktivität", "normal"),
        ("Test-User für alle 9 Rollen anlegen (nur Dev-Realm)", "normal"),
        ("Keycloak Admin API: Service-Account für backend/admin konfigurieren", "normal"),
        ("Keycloak Backup-Konfiguration (Realm-Export als JSON in Versionskontrolle)", "normal"),
        # Valkey
        ("Valkey 8.x Single-Instance für Dev (Docker)", "normal"),
        ("Valkey Cluster (6 Nodes: 3 Primary + 3 Replica) für Produktion", "high"),
        ("Kubernetes StatefulSet + Headless Service für Valkey", "normal"),
        ("Cluster-Auth: Passwort-Authentifizierung aktivieren", "normal"),
        ("Valkey Exporter für Prometheus Monitoring", "low"),
        ("Verwendungszwecke dokumentieren: Sessions, API-Cache, Rate-Limit-Counter, WebSocket-State", "low"),
        # NATS
        ("NATS 2.x Single-Instance für Dev (Docker)", "normal"),
        ("NATS JetStream Cluster (3 Nodes, Raft Consensus) für Produktion", "high"),
        ("Streams definieren: telemetry (24h), alarms (7d), bridge-status (24h)", "high"),
        ("Consumer Groups: alert-service (durable), api-ws-service (durable)", "high"),
        ("NATS-Authentifizierung: NKey oder Username/Password pro Service", "normal"),
        ("NATS Exporter für Prometheus Monitoring", "low"),
        ("Kubernetes StatefulSet + Headless Service für NATS", "normal"),
        # PostgreSQL HA
        ("Patroni 3.x Setup: 1 Primary + 2 Replicas", "high"),
        ("etcd als Distributed Config Store (oder Kubernetes API als DCS)", "high"),
        ("pgBouncer als Connection-Pooler (Transaction Pooling Mode)", "high"),
        ("Patroni REST-API absichern (Basic Auth)", "normal"),
        ("Switchover testen: Primary manuell failover → Replica in < 30s", "high"),
        ("Streaming Replication: max_wal_senders=3, wal_level=replica", "normal"),
        # pgBackRest
        ("pgBackRest: täglich Full Backup, stündlich inkrementell", "high"),
        ("Retention: 30 Tage täglich, 1 Jahr monatliche Archive", "normal"),
        ("Off-site Backup: verschlüsselt in S3 (Hetzner Object Storage oder AWS S3)", "high"),
        ("Backup-Restore-Test: monatlich automatisiert in Staging", "high"),
        ("Alerting bei Backup-Failure via Apprise", "normal"),
        # Observability
        ("Prometheus Scrape Configs für alle Services", "normal"),
        ("Grafana Dashboards: Platform-Overview, Database, NATS, Service Latency", "normal"),
        ("Loki Log Aggregation: Promtail auf allen Pods, Log-Labels: service, env, tenant_id", "normal"),
        ("Alerting Rules: Service Down, High Error Rate, DB Replication Lag, NATS Backlog", "high"),
        ("Grafana On-Call / Alertmanager: Eskalation bei kritischen Plattform-Alerts", "normal"),
        ("Retention: Prometheus 30 Tage, Loki 90 Tage", "low"),
        # Kubernetes & Helm
        ("Helm Charts für alle Services (values.yaml mit Dev/Staging/Prod Overrides)", "high"),
        ("PodDisruptionBudgets: minAvailable=2 für API, Ingest, Alert Services", "high"),
        ("HorizontalPodAutoscaler: CPU 70% → Scale up, für API + Ingest + Alert", "high"),
        ("Kubernetes NetworkPolicies: nur erlaubte Service-zu-Service Kommunikation", "normal"),
        ("Pod Security Standards: Restricted Profile für alle eigenen Services", "normal"),
        ("Liveness + Readiness + Startup Probes für alle Deployments", "high"),
        ("ResourceRequests + ResourceLimits für alle Container", "normal"),
        ("Namespace-Strategie: sirenwatch-prod, sirenwatch-staging, sirenwatch-dev", "normal"),
        # Secrets
        ("Docker Compose: .env Dateien + Docker Secrets", "normal"),
        ("Kubernetes: Kubernetes Secrets (Base64) für Staging", "normal"),
        ("Produktion: Sealed Secrets (kubeseal) oder HashiCorp Vault Injector", "high"),
        ("Keycloak Client Secrets, DB-Passwörter, NATS-Credentials niemals in Git", "critical"),
    ],
    "Datenbank": [
        ("Schema: tenants — id UUID PK, name, type ENUM(country/state/district/municipality), parent_id FK, country CHAR(2), metadata JSONB", "high"),
        ("Schema: devices — id UUID PK, tenant_id FK, name, type, decoder_profile_id FK, lat/lon DECIMAL, address, active BOOL", "high"),
        ("Schema: telemetry — TimescaleDB Hypertable, device_id+ts+key PK, value JSONB, raw_hex, decoded_status, decoded_label, profile_version_id", "high"),
        ("Schema: alarms — id UUID PK, device_id FK, tenant_id FK, severity ENUM, status ENUM, message, raw_event JSONB, acknowledged_at/by, ack_comment, resolved_at", "high"),
        ("Schema: users — id UUID PK, keycloak_id UNIQUE, email, display_name, tenant_id FK, role, active BOOL", "high"),
        ("Schema: audit_log — id BIGSERIAL PK, user_id FK, action, entity_type, entity_id, ts, ip INET, payload JSONB — append-only via Trigger", "high"),
        ("Schema: decoder_profiles — id UUID PK, tenant_id FK (NULL=built-in), name, description, version INT, rules JSONB, active BOOL", "high"),
        ("Schema: decoder_profile_versions — historischer Snapshot je Version", "normal"),
        ("Schema: notification_rules — id UUID PK, tenant_id FK, name, conditions JSONB, channels JSONB, escalation JSONB, active BOOL", "normal"),
        ("Schema: notification_history — rule_id FK, alarm_id FK, channel, recipient, status ENUM(sent/failed/skipped), error", "normal"),
        ("Schema: api_tokens — id UUID PK, user_id FK, name, token_hash UNIQUE, scope, expires_at, last_used_at, use_count, revoked", "normal"),
        ("Schema: bridges — id UUID PK, device_ids UUID[], token_hash UNIQUE, version, last_seen_at, ip INET, active BOOL", "high"),
        ("Index auf telemetry(device_id, ts DESC) — häufigste Abfrage", "high"),
        ("Index auf alarms(tenant_id, status, created_at DESC)", "normal"),
        ("Index auf devices(tenant_id, active)", "normal"),
        ("Index auf audit_log(entity_type, entity_id, ts DESC)", "normal"),
        ("Index auf api_tokens(token_hash) — für Token-Lookup bei jedem Request", "high"),
        ("GiST-Index auf devices(location) für geografische Abfragen (PostGIS)", "normal"),
        ("TimescaleDB Extension installieren und aktivieren", "high"),
        ("telemetry als Hypertable: chunk_time_interval = 1 day", "high"),
        ("Retention Policy: add_retention_policy('telemetry', 2 years)", "normal"),
        ("Compression Policy: add_compression_policy('telemetry', 7 days)", "normal"),
        ("Continuous Aggregates: telemetry_hourly, telemetry_daily", "normal"),
        ("Materialized Views für Uptime-Statistiken", "normal"),
        ("Alembic Setup in backend/api/migrations/", "high"),
        ("Initiale Migration: alle Tabellen", "high"),
        ("Audit-Log-Trigger-Migration: BEFORE UPDATE OR DELETE → RAISE EXCEPTION", "high"),
        ("Seed-Migration: Built-in Decoder-Profile (TETRA Status E000-E01F, Generic SDS)", "normal"),
        ("Seed-Migration: Initialer platform_admin-User (nur Dev)", "normal"),
        ("Alembic in CI/CD: automatisch 'alembic upgrade head' vor Tests", "normal"),
        ("pgBackRest Backup-Konfiguration", "high"),
        ("DB Backup Restore-Test: monatlich in Staging", "high"),
        ("Disaster Recovery Runbook schreiben", "high"),
    ],
    "Backend — Ingest API": [
        ("POST /api/v1/{device_token}/telemetry — ThingsBoard-kompatible URL, empfängt Bridge-Payloads", "critical"),
        ("POST /ingest/bridge/status — Bridge-Heartbeat (Hostname, Version, IP, Timestamp)", "high"),
        ("Token-Authentifizierung: device_token → Lookup in bridges Tabelle (Token-Hash Vergleich)", "critical"),
        ("Rate Limiting per Bridge-Token: max. 100 req/min (konfigurierbar)", "normal"),
        ("Payload-Validierung: Pflichtfelder prüfen, ungültige Payloads mit 400 ablehnen und loggen", "high"),
        ("Telemetrie in telemetry Hypertable schreiben (async, non-blocking)", "high"),
        ("Bridge-Status in bridges Tabelle aktualisieren (last_seen_at, ip)", "high"),
        ("NATS Publish bei jedem Event: telemetry.{device_id} Stream", "high"),
        ("NATS Publish bei Bridge-Status-Änderung: bridge-status.{bridge_id} Stream", "normal"),
        ("Offline-Detection vorbereiten: Event mit offline-Flag wenn kein Heartbeat für N Minuten", "high"),
        ("Fehler-Logging mit strukturiertem JSON (Loki-kompatibel)", "normal"),
        ("Prometheus Metrics: ingest_requests_total, ingest_latency_seconds, ingest_errors_total", "normal"),
    ],
    "Backend — Core API": [
        # Tenants
        ("GET /api/v1/tenants — Liste (gefiltert nach Caller-Scope)", "high"),
        ("GET /api/v1/tenants/{id} — Detail + Kinder-Tenants", "high"),
        ("POST /api/v1/tenants — Anlegen (nur platform_admin)", "high"),
        ("PUT /api/v1/tenants/{id} — Aktualisieren", "normal"),
        ("DELETE /api/v1/tenants/{id} — Deaktivieren (Soft-Delete)", "normal"),
        # Devices
        ("GET /api/v1/devices — Liste mit Filterung nach tenant_id, status, active", "high"),
        ("GET /api/v1/devices/{id} — Detail mit aktuellem Status", "high"),
        ("POST /api/v1/devices — Gerät anlegen", "high"),
        ("PUT /api/v1/devices/{id} — Gerät aktualisieren (Name, Koordinaten, Decoder-Profil)", "high"),
        ("DELETE /api/v1/devices/{id} — Gerät deaktivieren (Soft-Delete)", "normal"),
        ("GET /api/v1/devices/{id}/telemetry — Zeitreihe mit from/to/limit Parametern", "high"),
        ("GET /api/v1/devices/{id}/status — Letzter bekannter Status (aus Cache/DB)", "high"),
        # Alarms
        ("GET /api/v1/alarms — Liste mit Filter: status, severity, device_id, tenant_id, from, to", "high"),
        ("GET /api/v1/alarms/{id} — Detail", "normal"),
        ("POST /api/v1/alarms/{id}/acknowledge — Quittierung mit Pflichtkommentar", "high"),
        ("GET /api/v1/alarms/{id}/history — Statusverlauf eines Alarms", "normal"),
        # Users
        ("GET /api/v1/users — Liste (gefiltert nach Caller-Scope)", "normal"),
        ("GET /api/v1/users/{id} — Detail", "normal"),
        ("POST /api/v1/users — Nutzer anlegen + in Keycloak anlegen", "high"),
        ("PUT /api/v1/users/{id} — Rolle / Tenant ändern", "normal"),
        ("DELETE /api/v1/users/{id} — DSGVO-konformes Löschen", "high"),
        # Audit
        ("GET /api/v1/audit-log — mit Filter: user_id, action, entity_type, from, to", "normal"),
        ("GET /api/v1/audit-log/export — CSV-Download", "normal"),
        # Decoder Profiles
        ("GET /api/v1/decoder-profiles — Liste (eigene + Built-in)", "normal"),
        ("GET /api/v1/decoder-profiles/{id} — Detail mit Rules-JSON", "normal"),
        ("POST /api/v1/decoder-profiles — Neues Profil anlegen", "normal"),
        ("PUT /api/v1/decoder-profiles/{id} — Profil aktualisieren (neue Version anlegen)", "normal"),
        ("DELETE /api/v1/decoder-profiles/{id} — Deaktivieren (Built-in nicht löschbar)", "normal"),
        ("POST /api/v1/decoder-profiles/{id}/test — Testwert gegen Profil auswerten", "normal"),
        # Notification Rules
        ("GET /api/v1/notification-rules — Liste", "normal"),
        ("POST /api/v1/notification-rules — Regel anlegen", "normal"),
        ("PUT /api/v1/notification-rules/{id} — Regel aktualisieren", "normal"),
        ("DELETE /api/v1/notification-rules/{id} — Regel löschen", "normal"),
        ("POST /api/v1/notification-rules/{id}/test — Test-Benachrichtigung senden", "normal"),
        # API Tokens
        ("GET /api/v1/api-tokens — Liste eigener Tokens (Hashes, nie Klartext)", "normal"),
        ("POST /api/v1/api-tokens — Token generieren, Klartext einmalig zurückgeben", "normal"),
        ("DELETE /api/v1/api-tokens/{id} — Token widerrufen", "normal"),
        # Stats
        ("GET /api/v1/stats/overview — Zusammenfassung: Geräte total, online, alarm, offline", "high"),
        ("GET /api/v1/stats/uptime — Uptime-% pro Gerät/Tenant im Zeitraum", "normal"),
        ("GET /api/v1/stats/alarms/summary — Alarmhäufigkeit, MTTR, Typ-Verteilung", "normal"),
        # WebSocket
        ("WebSocket /ws/live — Real-time Telemetrie + Alarm-Events via NATS → WS", "high"),
        ("WebSocket: JWT-Authentifizierung im Authorization Header oder ?token= Query-Param", "high"),
        ("WebSocket: Scope-Filterung — Nutzer bekommt nur Events seines Tenant-Scopes", "high"),
        ("WebSocket: Reconnect-Logik auf Client-Seite", "normal"),
        # General
        ("FastAPI-App-Struktur: Router, Dependencies, Middleware, Exception Handlers", "high"),
        ("JWT-Validierung via Keycloak JWKS (automatische Key-Rotation)", "high"),
        ("Tenant-Scope-Middleware: Prüft Zugriff bei jedem Request", "high"),
        ("Paginierung für alle Listen-Endpoints (page, page_size, cursor)", "normal"),
        ("Einheitliches Fehlerformat: { error, detail, code }", "normal"),
        ("OpenAPI Tags und Beschreibungen für alle Endpoints", "low"),
        ("Prometheus Metrics: Request-Latenz, Error-Rate, Endpoint-Aufrufe", "normal"),
        ("Structured Logging (JSON, Loki-kompatibel)", "normal"),
    ],
    "Backend — Alert Service": [
        ("NATS JetStream Consumer: telemetry.* Stream abonnieren (durable Consumer)", "high"),
        ("NATS JetStream Consumer: bridge-status.* Stream abonnieren", "high"),
        ("Regelengine: Threshold-Regel (Wert > Schwellwert)", "high"),
        ("Regelengine: Status-Change-Regel (Übergang von Status A → Status B)", "high"),
        ("Regelengine: Offline-Detection (kein Event für X Minuten — Cron-basiert)", "high"),
        ("Regelengine: Kombinations-Regeln (AND/OR via JSON-Condition-Objekte)", "normal"),
        ("Alarm anlegen: Regel matcht → Alarm-Record in alarms Tabelle", "high"),
        ("Alarm-Deduplizierung: kein doppelter Alarm wenn Status sich nicht ändert", "high"),
        ("Alarm-Recovery: automatisch resolved wenn Status wieder OK", "high"),
        ("Apprise-Integration: Notification senden bei Alarm-Erstellung", "high"),
        ("Eskalationsketten: Stufe 1 → 2 → 3 nach delay_minutes — asyncio.sleep Task", "normal"),
        ("Eskalations-Abbruch: stoppen wenn Alarm quittiert oder gelöst", "normal"),
        ("Notification-History: jede Benachrichtigung in notification_history speichern", "normal"),
        ("Fehlerbehandlung: Apprise-Fehler loggen, Retry mit Backoff (3 Versuche)", "normal"),
        ("Prometheus Metrics: alerts_created_total, notifications_sent_total, escalation_triggered_total", "low"),
    ],
    "Frontend": [
        # Setup
        ("Next.js 15 Projekt anlegen (App Router, TypeScript strict, Tailwind CSS)", "critical"),
        ("shadcn/ui initialisieren (CSS Variables Modus)", "high"),
        ("Design System: CSS-Variablen für alle Farbtoken (bg-base, accent-red, status-*)", "high"),
        ("Tailwind Config: Custom Colors, Monospace-Fontstack (SirenWatch Branding)", "high"),
        ("next-intl Setup: Deutsch (Standard) + Englisch", "normal"),
        ("TanStack React Query Setup: QueryClient mit Stale-Time 30s", "high"),
        ("Keycloak OIDC Integration: oidc-client-ts oder next-auth mit Keycloak Provider", "high"),
        ("Axios/Fetch-Wrapper mit automatischem JWT Refresh und Auth-Error-Redirect", "high"),
        ("Airbus-style Sirenen-SVG-Icons in 5 Zuständen: OK, Alarm, Sabotage, Fehler, Offline", "high"),
        ("Toast-Notification-System (shadcn/ui Sonner) für API-Fehler und Erfolg-Feedback", "normal"),
        # Navigation
        ("Root Layout: Navigation, Sidebar, Main Content, Footer", "high"),
        ("Navigation: Logo, Hauptmenü, User-Dropdown, Tenant-Breadcrumb", "high"),
        ("Sidebar: kollabierbar, Menüpunkte je nach Rolle", "normal"),
        ("Responsive Breakpoints: Mobile (Hamburger), Tablet (schmale Sidebar), Desktop (breite Sidebar)", "high"),
        ("Protected Route: Redirect auf Login wenn nicht authentifiziert", "high"),
        # Login
        ("Login-Seite: SirenWatch Logo, 'Mit Keycloak anmelden' Button", "high"),
        ("Keycloak OIDC Redirect Flow", "high"),
        ("Nach Login: Redirect auf zuletzt besuchte Seite (PKCE State)", "normal"),
        ("Logout: Token-Invalidierung in Keycloak + lokale Session löschen", "normal"),
        # Karte
        ("Leaflet + react-leaflet Setup (SSR-safe dynamic import)", "high"),
        ("OpenStreetMap Tile-Layer (mit Fallback auf CDN)", "high"),
        ("Geräte als Airbus-Siren-Icons auf Karte platzieren", "high"),
        ("Marker-Cluster: Farbe = schlechtester Status im Cluster", "high"),
        ("Click auf Icon: Popup mit Name, Status, Zeitstempel, Link zur Detailseite", "normal"),
        ("Filterpanel: Land, Bundesland, Landkreis, Status", "normal"),
        ("Vollbild-Modus-Button", "low"),
        ("Echtzeit-Updates: WebSocket-Events aktualisieren Marker-Farben ohne Reload", "high"),
        # Status Grid
        ("Kachel-Komponente: farbiges Quadrat (10-40px), Tooltip mit Gerätename bei Hover", "high"),
        ("Gitter-Layout: Bundesland-Sektionen als Trennüberschriften", "high"),
        ("Kachel-Größe konfigurierbar (Slider: micro/small/medium/large)", "normal"),
        ("Sortierung: nach Bundesland, dann alphabetisch", "normal"),
        ("Alarmzustand: CSS animation pulse auf roten Kacheln", "normal"),
        ("WebSocket-Updates: Status ändert sich → Kachelfarbe animiert wechseln", "high"),
        ("'Letztes Update' Timestamp oben rechts", "low"),
        # Bundesland-Dashboard
        ("Treemap aller Landkreise (ECharts): Fläche proportional zu Geräteanzahl, Farbe = Status", "high"),
        ("KPI-Header: Gesamt, Online, Alarm, Sabotage, Offline, Uptime %", "high"),
        ("Letzter Alarm: Gerätename + Zeitstempel", "normal"),
        ("Click auf Landkreis-Block: Drill-down zur Landkreis-Übersicht", "normal"),
        ("Zeitraum-Selector für Uptime-KPI: 24h, 7d, 30d", "normal"),
        # Geräteliste
        ("Tabelle: Name, Tenant-Pfad, Status, Letztes Update, Decoder-Profil", "normal"),
        ("Suchfeld: Filter nach Name (Client-side)", "normal"),
        ("Dropdown-Filter: Status, Bundesland", "normal"),
        ("Sortierung: alle Spalten sortierbar", "normal"),
        ("Paginierung (server-seitig)", "normal"),
        ("'Neues Gerät' Button (nur für district_admin+)", "normal"),
        # Gerät-Detail
        ("Header: Name, Status-Badge, Tenant-Breadcrumb", "normal"),
        ("Kleine Karte: Gerät-Pin, Adresse via Nominatim Reverse Geocoding", "normal"),
        ("Telemetrie-Chart (ECharts Line): Zeitreihe mit Zeitraum-Picker 1h/6h/24h/7d/30d", "high"),
        ("Status-History-Tabelle: Zeitstempel, SDS-Rohwert, Decoded Status, Label", "high"),
        ("Alarm-History-Tabelle: alle Alarme des Geräts mit Quittierungsinfo", "normal"),
        ("Konfigurationsabschnitt: Decoder-Profil-Dropdown, Koordinaten, Aktiv-Toggle", "normal"),
        ("API-Info-Block: Device-ID, letzter Ingest-Zeitstempel, Bridge-Version", "low"),
        ("Speichern-Button mit Bestätigung (nur district_admin+)", "normal"),
        # Alarm Center
        ("Tab Aktiv: Tabelle mit Severity-Icon, Gerätename, Nachricht, Zeitstempel, Quittierungs-Button", "high"),
        ("Quittierungs-Dialog: Pflichtkommentar (min. 10 Zeichen), Bestätigung", "high"),
        ("Tab History: Filter nach Zeitraum, Tenant, Severity; Export als CSV", "normal"),
        ("Severity-Sortierung: Alarm → Error → Warning → Info", "normal"),
        ("Echtzeit-Update: neue Alarme ohne Seiten-Reload (WebSocket)", "high"),
        ("Alarm-Count-Badge in Navigation (Anzahl aktiver Alarme)", "high"),
        # Admin
        ("Admin: Tenant-Hierarchie als Baumansicht (rekursive Komponente)", "normal"),
        ("Admin: Tenant anlegen Modal (Name, Typ, Parent)", "normal"),
        ("Admin: Nutzer-Tabelle mit Email, Rolle, Tenant, Aktiv-Status", "normal"),
        ("Admin: Rolle ändern per Dropdown", "normal"),
        ("Admin: Nutzer einladen per E-Mail (Keycloak Einladungsmail)", "normal"),
        ("Admin: Decoder-Profile-Editor — Tabelle der Rules mit Live-Preview", "high"),
        ("Admin: Decoder Import (JSON) + Export (JSON) mit Validierung", "normal"),
        ("Admin: Notification Rules Editor — Condition Builder + Kanal-Konfigurator", "normal"),
        ("Admin: Test-Button — Test-Benachrichtigung über alle Kanäle senden", "normal"),
        ("Admin: API-Token-Liste, Token erstellen (einmalige Klartextanzeige), Token widerrufen", "normal"),
        # Audit Log
        ("Audit-Log-Viewer: Tabelle mit Zeitstempel, User, Aktion, Entity, IP", "normal"),
        ("Audit-Log: Filter Zeitraum + User + Aktion", "normal"),
        ("Audit-Log: Expandable Row mit vollständigem payload-JSON", "normal"),
        ("Audit-Log: CSV-Download (gefilterte Daten)", "normal"),
        # Reports
        ("Reports: Tenant/Zeitraum-Picker (Scope-basiert)", "normal"),
        ("Reports: Uptime-Tabelle pro Gerät", "normal"),
        ("Reports: Alarm-Statistiken Pie Chart (ECharts)", "normal"),
        ("Reports: PDF Export via WeasyPrint", "normal"),
        ("Reports: CSV Export Rohdaten", "normal"),
        # Allgemein
        ("Responsive: Mobile (360px+), Tablet (768px+), Desktop (1280px+), Widescreen (2560px+)", "critical"),
        ("Keyboard Navigation: alle Elemente per Tab erreichbar", "normal"),
        ("Accessibility: WCAG 2.1 AA — Kontrast, ARIA-Labels, Focus-Styles", "normal"),
        ("Error Boundaries: React Error Boundary auf jeder Seite", "normal"),
        ("Loading States: Skeleton-Screens für alle Datenfetch-Komponenten", "normal"),
        ("Empty States: sinnvolle Meldung wenn keine Daten", "low"),
        ("Browserkompatibilität: Chrome, Firefox, Safari, Edge (aktuelle Versionen)", "normal"),
        ("PageSpeed/Lighthouse: Performance >= 80, Accessibility >= 90", "normal"),
    ],
    "SDS Decoder": [
        ("Decoder-Profil-Datenmodell finalisieren: rules[] mit ai_service, hex_min, hex_max, status, label, sabotage, uebertemp", "high"),
        ("Built-in Profil: 'TETRA Status E000-E01F' in DB anlegen (aus bestehender Codebase)", "high"),
        ("Built-in Profil: 'Generic SDS' anlegen (Hex als Label, Status = unknown)", "normal"),
        ("Decoder-Library extrahieren: standalone siren_decoder.py mit decode(hex, profile) -> DecodedEvent", "high"),
        ("Unit Tests für Decoder-Library: alle bekannten Codes + Edge-Cases (Bereichsgrenzen)", "high"),
        ("UI: Hex-Range-Editor mit Validierung (Format-Check, Min <= Max)", "normal"),
        ("UI: Live-Preview-API-Call (POST /api/v1/decoder-profiles/{id}/test)", "normal"),
        ("UI: Drag & Drop Sortierung der Rules (Priorität bei überlappenden Ranges)", "low"),
        ("Import: JSON-Schema-Validierung mit aussagekräftigen Fehlermeldungen", "normal"),
        ("Export: JSON-Download mit vollständigem Profil inkl. Metadaten", "normal"),
        ("Profil einem Gerät zuweisen: Dropdown in Gerät-Detailseite", "normal"),
        ("Profil einem Tenant zuweisen (vererbt an alle Geräte des Tenants)", "normal"),
        ("Versionierung: bei jeder Änderung neuen Snapshot in decoder_profile_versions", "normal"),
        ("Historische Telemetrie: profile_version_id FK in telemetry (für Retroaudit)", "normal"),
        ("Migrations-Skript: bestehende Hardcode-Konstanten in DB-Profil überführen", "high"),
    ],
    "Security & Compliance": [
        # Auth
        ("MFA aktivieren: Pflicht (Required Action) für platform_admin, country_admin, state_admin, district_admin", "critical"),
        ("MFA-Methoden: TOTP (Google Authenticator, Authy) + WebAuthn (Hardware Key, Passkey)", "high"),
        ("SAML 2.0 Identity Provider in Keycloak (Konfigurationsvorlage für Behörden-AD)", "high"),
        ("LDAP/AD Connector in Keycloak: User Federation Setup (Konfigurationsvorlage)", "normal"),
        ("AD-Gruppen → Keycloak Rollen Mapping dokumentieren und testen", "normal"),
        ("Token-Lifetime Review: Access 15min, Refresh 12h (kein Remember me für Admin-Rollen)", "high"),
        ("Brute-Force-Schutz: 5 Fehlversuche → 15 Min Lockout", "high"),
        # Netzwerk
        ("Traefik: Rate Limiting Middleware (global + per-IP)", "high"),
        ("Traefik: Security Headers (HSTS max-age=63072000, CSP, X-Frame-Options DENY, nosniff, Referrer-Policy)", "high"),
        ("CORS konfigurieren: nur erlaubte Origins (Produktions-Domain + Staging)", "high"),
        ("Interne Service-zu-Service Verbindungen nur über internes Kubernetes-Netzwerk", "high"),
        ("TLS 1.3 Minimum für alle externen Verbindungen", "high"),
        ("Kubernetes NetworkPolicies für alle Namespaces", "normal"),
        # Audit & Integrität
        ("Audit-Log Append-Only Trigger: BEFORE UPDATE OR DELETE → RAISE EXCEPTION", "critical"),
        ("Audit-Log-Streaming: an externe Stelle (S3-verschlüsselt oder SIEM)", "high"),
        ("Hash-Chain: jeder Audit-Log-Eintrag enthält SHA256 des Vorgänger-Eintrags", "normal"),
        # DSGVO
        ("Nutzer-Datenlöschung: DELETE ersetzt Email/Name durch [GELOESCHT-{uuid}], Audit Log bleibt", "high"),
        ("AVV-Vorlage erstellen: Word/PDF-Template im Admin Panel abrufbar", "high"),
        ("Datenschutz-Hinweis in Frontend-Footer mit Link zur Datenschutzerklärung", "normal"),
        ("Datenverarbeitungsverzeichnis (VVT): /docs/legal/vvt.md", "high"),
        # OWASP
        ("OWASP Top 10 Checkliste abarbeiten (/docs/security/owasp-review.md)", "high"),
        ("SAST: Semgrep in CI-Pipeline, blockiert bei CRITICAL/HIGH", "high"),
        ("Container-Scan: Trivy in CI-Pipeline, blockiert bei kritischen CVEs", "high"),
        ("Dependency-Scan: Dependabot + Safety (Python) + npm audit", "normal"),
        ("Input Validation: alle Endpoints mit Pydantic (Python) / Zod (TypeScript)", "high"),
        ("SQL Injection: ausschließlich parametrisierte Queries (SQLAlchemy)", "high"),
        ("XSS Prevention: React escaping + CSP Header", "high"),
        ("Penetration-Test-Vorbereitung: Scope-Dokument, Responsible-Disclosure-Policy", "high"),
        ("Jährlicher Penetrations-Test (extern, akkreditiert): nach Phase 6", "high"),
        # BSI
        ("BSI IT-Grundschutz Mapping-Dokument: /docs/compliance/bsi-grundschutz-mapping.md", "high"),
        ("Bausteine abdecken: OPS.1.1.2, OPS.1.1.3, CON.3, NET.1.1, APP.3.1, INF.1, ISMS.1", "high"),
        ("Review durch TJK-Solutions Geschäftsführung", "high"),
    ],
    "Dokumentation": [
        ("FastAPI OpenAPI-Beschreibungen: alle Endpoints mit Summary, Description, Response-Schemas", "normal"),
        ("GET /docs (Swagger UI) und GET /redoc in Produktion nur für Admins zugänglich", "normal"),
        ("OpenAPI JSON exportieren + in Docs versionieren (/docs/api/openapi.json)", "low"),
        ("Docker Compose Quick-Start Guide (/docs/deployment/docker-compose.md)", "high"),
        ("Kubernetes/Helm Deployment Guide (/docs/deployment/kubernetes.md)", "high"),
        ("TLS/SSL Setup mit Let's Encrypt (/docs/deployment/tls.md)", "normal"),
        ("Keycloak Initial Setup Guide (/docs/deployment/keycloak-setup.md)", "high"),
        ("Benutzer-Handbuch: Login, Navigation, Karte (/docs/user/01-grundlagen.md)", "normal"),
        ("Benutzer-Handbuch: Status Grid / NOC View", "normal"),
        ("Benutzer-Handbuch: Alarm Center + Quittierung", "normal"),
        ("Benutzer-Handbuch: Reports und Export", "low"),
        ("Screenshots aller UI-Module (automatisch via Playwright)", "low"),
        ("Admin-Handbuch: Tenant-Hierarchie verwalten", "normal"),
        ("Admin-Handbuch: Nutzer anlegen und Rollen zuweisen", "normal"),
        ("Admin-Handbuch: Decoder-Profile erstellen und zuweisen", "normal"),
        ("Admin-Handbuch: Notification Rules konfigurieren", "normal"),
        ("Admin-Handbuch: API-Tokens verwalten", "low"),
        ("Admin-Handbuch: Backup & Recovery", "high"),
        ("Migrations-Guide ThingsBoard → SirenWatch: URL-Konfiguration Bridge ändern", "high"),
        ("Migrations-Guide: Datenexport aus ThingsBoard (Gerätehistorie)", "normal"),
        ("Migrations-Guide: Datenimport in SirenWatch (Migrations-Skript)", "normal"),
        ("Migrations-Guide: Decoder-Profil-Migration (Hardcode → DB-Profil)", "normal"),
        ("Migrations-Guide: Rollback-Anleitung (Fallback auf ThingsBoard)", "normal"),
        ("Decoder-Guide: Einführung — Was ist ein Decoder-Profil", "low"),
        ("Decoder-Guide: Neues Profil anlegen, Regeln definieren", "normal"),
        ("Decoder-Guide: Profil importieren/exportieren", "low"),
        ("Decoder-Guide: Beispiel Hoermann DSP624 vollständiges Profil", "normal"),
        ("Runbook: /docs/runbooks/runbook-platform-outage.md", "high"),
        ("Runbook: /docs/runbooks/runbook-data-breach.md", "critical"),
        ("Runbook: /docs/runbooks/runbook-db-failover.md", "high"),
        ("Runbook: /docs/runbooks/runbook-bridge-offline-massenausfall.md", "high"),
        ("Runbook: /docs/runbooks/runbook-keycloak-unavailable.md", "high"),
        ("Alle Runbooks von zweiter Person durchgespielt und signiert", "high"),
    ],
}


def seed(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")

    # Prüfen ob bereits Daten vorhanden
    existing = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    if existing > 0:
        print(f"Datenbank enthält bereits {existing} Projekt(e). Abgebrochen (--force zum Überschreiben).")
        conn.close()
        return

    now = int(time.time() * 1000)
    total_tasks = 0

    for proj in PROJECTS:
        cur = conn.execute(
            "INSERT INTO projects (name, description, color, created_at) VALUES (?,?,?,?)",
            (proj["name"], proj["description"], proj["color"], now)
        )
        project_id = cur.lastrowid
        tasks = TASKS.get(proj["name"], [])

        for title, priority in tasks:
            conn.execute(
                """INSERT INTO tasks (project_id, title, status, priority, created_at, updated_at)
                   VALUES (?,?,'todo',?,?,?)""",
                (project_id, title, priority, now, now)
            )
            total_tasks += 1

        print(f"  ✓ {proj['name']:35s} — {len(tasks):3d} Aufgaben")

    conn.commit()
    conn.close()
    print(f"\n✅ {len(PROJECTS)} Projekte, {total_tasks} Aufgaben eingefügt.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None, help="Pfad zur pm.db (default: ./pm.db)")
    ap.add_argument("--force", action="store_true", help="Auch wenn bereits Daten vorhanden")
    args = ap.parse_args()

    db_path = Path(args.db) if args.db else Path(__file__).parent / "pm.db"
    if not db_path.exists():
        print(f"Datenbank nicht gefunden: {db_path}")
        print("Starte zuerst app.py einmal damit die DB angelegt wird.")
        exit(1)

    if args.force:
        conn = sqlite3.connect(db_path)
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM projects")
        conn.commit()
        conn.close()
        print("Bestehende Daten gelöscht.")

    print(f"Befülle {db_path} ...\n")
    seed(db_path)
