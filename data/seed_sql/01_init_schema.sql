-- =============================================================================
-- OpsAgent: Operational Database Schema
-- Coal Distribution & Logistics Operations (PT Nusantara Coal Operations)
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing tables for fresh initialization
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS barge_shipments CASCADE;
DROP TABLE IF EXISTS coal_inventory CASCADE;
DROP TABLE IF EXISTS stockpiles CASCADE;
DROP TABLE IF EXISTS barges CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;

-- 1. Master Customers (Buyer Batubara)
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    customer_code VARCHAR(20) UNIQUE NOT NULL,
    company_name VARCHAR(150) NOT NULL,
    industry_type VARCHAR(50) NOT NULL, -- 'PLTU', 'SEMEN', 'SMELTER_NICKEL', 'TRADING'
    pic_name VARCHAR(100) NOT NULL,
    pic_phone VARCHAR(30) NOT NULL,
    pic_email VARCHAR(100) NOT NULL,
    delivery_port VARCHAR(100) NOT NULL,
    payment_term_days INT DEFAULT 30,
    credit_limit_usd NUMERIC(15, 2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Master Suppliers (Concession & Pit Tambang)
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    supplier_code VARCHAR(20) UNIQUE NOT NULL,
    company_name VARCHAR(150) NOT NULL,
    concession_area VARCHAR(100) NOT NULL,
    pit_location VARCHAR(100) NOT NULL,
    pic_name VARCHAR(100) NOT NULL,
    pic_phone VARCHAR(30) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE', -- 'ACTIVE', 'SUSPENDED'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Master Stockpiles & Jetty
CREATE TABLE stockpiles (
    id SERIAL PRIMARY KEY,
    stockpile_code VARCHAR(20) UNIQUE NOT NULL,
    stockpile_name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    province VARCHAR(50) NOT NULL,
    max_capacity_mt NUMERIC(12, 2) NOT NULL,
    current_stock_mt NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    manager_name VARCHAR(100) NOT NULL,
    contact_phone VARCHAR(30) NOT NULL,
    status VARCHAR(20) DEFAULT 'OPERATIONAL', -- 'OPERATIONAL', 'MAINTENANCE', 'FULL'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Inventory Batubara per Stockpile & Grade
CREATE TABLE coal_inventory (
    id SERIAL PRIMARY KEY,
    stockpile_id INT NOT NULL REFERENCES stockpiles(id) ON DELETE CASCADE,
    grade VARCHAR(20) NOT NULL, -- e.g. 'GAR 3800', 'GAR 4200', 'GAR 5000'
    calorific_value_gar INT NOT NULL, -- kcal/kg
    total_moisture_pct NUMERIC(5, 2) NOT NULL,
    ash_content_pct NUMERIC(5, 2) NOT NULL,
    total_sulfur_pct NUMERIC(5, 2) NOT NULL,
    tonnage_mt NUMERIC(12, 2) NOT NULL,
    batch_number VARCHAR(50) NOT NULL,
    supplier_id INT REFERENCES suppliers(id),
    last_survey_date DATE NOT NULL,
    temperature_celsius NUMERIC(5, 2) DEFAULT 38.5, -- critical for self-combustion check
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Master Tongkang & Tugboat (Barging)
CREATE TABLE barges (
    id SERIAL PRIMARY KEY,
    barge_code VARCHAR(20) UNIQUE NOT NULL,
    barge_name VARCHAR(100) NOT NULL,
    tugboat_name VARCHAR(100) NOT NULL,
    capacity_feet INT NOT NULL, -- e.g. 300 feet, 330 feet
    max_capacity_mt NUMERIC(10, 2) NOT NULL,
    owner_company VARCHAR(100) NOT NULL,
    status VARCHAR(30) DEFAULT 'AVAILABLE', -- 'AVAILABLE', 'IN_TRANSIT', 'LOADING', 'MAINTENANCE'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Pengiriman Tongkang (Barge Shipments / Transhipment)
CREATE TABLE barge_shipments (
    id SERIAL PRIMARY KEY,
    shipment_number VARCHAR(30) UNIQUE NOT NULL,
    barge_id INT NOT NULL REFERENCES barges(id),
    customer_id INT NOT NULL REFERENCES customers(id),
    stockpile_origin_id INT NOT NULL REFERENCES stockpiles(id),
    coal_grade VARCHAR(20) NOT NULL,
    tonnage_loaded_mt NUMERIC(10, 2) NOT NULL,
    origin_jetty VARCHAR(100) NOT NULL,
    destination_port VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL, -- 'LOADING', 'SAILING', 'DISCHARGING', 'COMPLETED', 'ANCHORED'
    etd TIMESTAMP WITH TIME ZONE NOT NULL,
    eta TIMESTAMP WITH TIME ZONE NOT NULL,
    actual_arrival TIMESTAMP WITH TIME ZONE,
    surveyor_company VARCHAR(100) DEFAULT 'PT Surveyor Indonesia',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Audit Log Table (Observability & Compliance)
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    trace_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(64),
    user_id VARCHAR(50) NOT NULL,
    user_role VARCHAR(20) NOT NULL, -- 'staff', 'manager'
    user_query TEXT NOT NULL,
    routed_intent VARCHAR(50),
    tool_name VARCHAR(50),
    tool_arguments JSONB,
    tool_result_summary TEXT,
    execution_status VARCHAR(20) NOT NULL, -- 'SUCCESS', 'FAILED', 'PENDING_APPROVAL', 'REJECTED'
    latency_ms NUMERIC(10, 2) NOT NULL,
    prompt_tokens INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    estimated_cost_usd NUMERIC(10, 6) DEFAULT 0.000000,
    pii_masked BOOLEAN DEFAULT FALSE,
    guardrail_flagged BOOLEAN DEFAULT FALSE,
    guardrail_reason VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indices for rapid querying
CREATE INDEX idx_coal_inventory_stockpile ON coal_inventory(stockpile_id);
CREATE INDEX idx_coal_inventory_grade ON coal_inventory(grade);
CREATE INDEX idx_shipments_status ON barge_shipments(status);
CREATE INDEX idx_shipments_customer ON barge_shipments(customer_id);
CREATE INDEX idx_audit_log_trace ON audit_log(trace_id);
CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);

-- =============================================================================
-- Read-Only Database User Setup (Security Guardrail for text-to-SQL)
-- =============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'opsagent_ro') THEN
        CREATE ROLE opsagent_ro WITH LOGIN PASSWORD 'opsagent_ro_password';
    END IF;
END
$$;

-- Grant SELECT only on operational tables; strictly prohibit DDL & DML
GRANT CONNECT ON DATABASE opsagent_db TO opsagent_ro;
GRANT USAGE ON SCHEMA public TO opsagent_ro;
GRANT SELECT ON customers, suppliers, stockpiles, coal_inventory, barges, barge_shipments TO opsagent_ro;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA public FROM opsagent_ro;
