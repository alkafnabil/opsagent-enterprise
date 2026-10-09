-- =============================================================================
-- OpsAgent: Seed Data for Coal Logistics Operations
-- PT Nusantara Coal Operations
-- =============================================================================

-- 1. Insert Customers
INSERT INTO customers (customer_code, company_name, industry_type, pic_name, pic_phone, pic_email, delivery_port, payment_term_days, credit_limit_usd) VALUES
('CUST-PLN-01', 'PT PLN Energi Primer Indonesia', 'PLTU', 'Bambang Sudiro', '081299882341', 'bambang.sudiro@plnepi.co.id', 'Pelabuhan PLTU Suralaya, Banten', 45, 5000000.00),
('CUST-PLN-02', 'PT Pembangkitan Jawa Bali (PJB)', 'PLTU', 'Rahmat Hidayat', '081388771122', 'rahmat.h@pjb.co.id', 'Pelabuhan PLTU Paiton, Jawa Timur', 45, 4500000.00),
('CUST-SMN-01', 'PT Semen Indonesia (Persero) Tbk', 'SEMEN', 'Agus Setiawan', '081177665544', 'agus.s@sig.id', 'Pelabuhan Khusus Tuban, Jawa Timur', 30, 2000000.00),
('CUST-SMN-02', 'PT Semen Tonasa', 'SEMEN', 'Faisal Baharuddin', '081255443322', 'faisal.b@sementonasa.co.id', 'Pelabuhan Biringkassi, Sulawesi Selatan', 30, 1500000.00),
('CUST-NCK-01', 'PT Gunbuster Nickel Industry', 'SMELTER_NICKEL', 'Hendro Wijaya', '081822334455', 'hendro.w@gni-smelter.com', 'Jetty Morowali Utara, Sulawesi Tengah', 14, 3000000.00),
('CUST-NCK-02', 'PT Huadi Nickel-Alloy Indonesia', 'SMELTER_NICKEL', 'Denny Kurniawan', '081733445566', 'denny.k@huadinickel.com', 'Kawasan Industri Bantaeng, Sulawesi Selatan', 14, 2500000.00);

-- 2. Insert Suppliers
INSERT INTO suppliers (supplier_code, company_name, concession_area, pit_location, pic_name, pic_phone, status) VALUES
('SUP-KPC-01', 'PT Kaltim Prima Mining Concession', 'Sangatta North Block', 'Pit Hatari North', 'Iskandar Zulkarnaen', '081244556677', 'ACTIVE'),
('SUP-BRU-02', 'PT Berau Coal Perkasa', 'Lati Mine Block', 'Pit Central Lati', 'Budi Santoso', '081377889900', 'ACTIVE'),
('SUP-BRT-03', 'PT Barito Sumber Energi', 'Muara Teweh River Concession', 'Pit Danau Rayo', 'Wahyu Pratama', '081211223344', 'ACTIVE'),
('SUP-MBL-04', 'PT Mitra Batubara Kalsel', 'Tanah Bumbu Concession', 'Pit Angsana Block C', 'Dedi Mulyadi', '081566778899', 'ACTIVE');

-- 3. Insert Stockpiles
INSERT INTO stockpiles (stockpile_code, stockpile_name, location, province, max_capacity_mt, current_stock_mt, manager_name, contact_phone, status) VALUES
('STK-PLR-01', 'Stockpile Palaran Jetty', 'Palaran, Sungai Mahakam, Samarinda', 'Kalimantan Timur', 150000.00, 84500.00, 'Surya Darmawan', '081290807060', 'OPERATIONAL'),
('STK-KRG-02', 'Stockpile Kariangau Interport', 'Kariangau, Teluk Balikpapan', 'Kalimantan Timur', 250000.00, 192000.00, 'Handoko Prasetyo', '081380706050', 'OPERATIONAL'),
('STK-TSK-03', 'Stockpile Trisakti Port', 'Trisakti, Sungai Barito, Banjarmasin', 'Kalimantan Selatan', 120000.00, 67200.00, 'Ahmad Fauzi', '081190708090', 'OPERATIONAL'),
('STK-MTW-04', 'Stockpile Muara Teweh Riverbank', 'Muara Teweh, Barito Utara', 'Kalimantan Tengah', 80000.00, 31800.00, 'Rian Hidayatullah', '081270809010', 'OPERATIONAL'),
('STK-TBN-05', 'Taboneo Transhipment Anchorage', 'Perairan Taboneo, Muara Barito', 'Kalimantan Selatan', 500000.00, 310500.00, 'Capt. Aris Munandar', '081160708020', 'OPERATIONAL');

-- 4. Insert Coal Inventory (Batubara per Stockpile)
INSERT INTO coal_inventory (stockpile_id, grade, calorific_value_gar, total_moisture_pct, ash_content_pct, total_sulfur_pct, tonnage_mt, batch_number, supplier_id, last_survey_date, temperature_celsius) VALUES
(1, 'GAR 4200', 4210, 34.2, 5.8, 0.42, 42500.00, 'BATCH-PLR-2026-03A', 1, '2026-04-01', 39.2),
(1, 'GAR 5000', 5025, 26.5, 7.1, 0.65, 42000.00, 'BATCH-PLR-2026-03B', 2, '2026-04-02', 41.0),
(2, 'GAR 3800', 3820, 38.0, 6.2, 0.35, 95000.00, 'BATCH-KRG-2026-04A', 4, '2026-04-03', 37.5),
(2, 'GAR 4200', 4190, 34.8, 5.5, 0.38, 97000.00, 'BATCH-KRG-2026-04B', 1, '2026-04-04', 43.5), -- Waspada suhu > 42 C
(3, 'GAR 4200', 4220, 33.9, 5.9, 0.45, 37200.00, 'BATCH-TSK-2026-03A', 3, '2026-04-02', 38.0),
(3, 'GAR 4600', 4615, 29.8, 6.4, 0.52, 30000.00, 'BATCH-TSK-2026-03B', 3, '2026-04-03', 44.8), -- Panas/Self-combustion alert
(4, 'GAR 3800', 3790, 38.5, 6.0, 0.30, 31800.00, 'BATCH-MTW-2026-04A', 3, '2026-04-05', 36.5),
(5, 'GAR 4200', 4205, 34.0, 5.6, 0.40, 180500.00, 'BATCH-TBN-2026-04A', 1, '2026-04-06', 38.5),
(5, 'GAR 5000', 5040, 26.2, 7.3, 0.60, 130000.00, 'BATCH-TBN-2026-04B', 2, '2026-04-06', 40.2);

-- 5. Insert Barges & Tugboats
INSERT INTO barges (barge_code, barge_name, tugboat_name, capacity_feet, max_capacity_mt, owner_company, status) VALUES
('BG-301', 'BG Trans Coal 301', 'TB Rajawali 08', 300, 8000.00, 'PT Trans Coal Logistik', 'IN_TRANSIT'),
('BG-302', 'BG Trans Coal 302', 'TB Perkasa 12', 300, 8000.00, 'PT Trans Coal Logistik', 'AVAILABLE'),
('BG-330', 'BG Nusantara 330', 'TB Mega Marine 02', 330, 10500.00, 'PT Samudera Bahari Line', 'IN_TRANSIT'),
('BG-280', 'BG Mahakam Jaya 280', 'TB Borneo Star 05', 280, 6500.00, 'PT Mahakam Armada Mandiri', 'LOADING'),
('BG-305', 'BG Barito Energy 305', 'TB Bintang Samudera', 300, 8200.00, 'PT Barito Shipping Lines', 'IN_TRANSIT');

-- 6. Insert Barge Shipments
INSERT INTO barge_shipments (shipment_number, barge_id, customer_id, stockpile_origin_id, coal_grade, tonnage_loaded_mt, origin_jetty, destination_port, status, etd, eta, actual_arrival, surveyor_company) VALUES
('SHP-2026-0401', 1, 1, 1, 'GAR 4200', 7850.00, 'Palaran Jetty, Samarinda', 'Pelabuhan PLTU Suralaya, Banten', 'SAILING', NOW() - INTERVAL '3 days', NOW() + INTERVAL '2 days', NULL, 'PT Carsurin'),
('SHP-2026-0402', 3, 2, 2, 'GAR 5000', 10200.00, 'Kariangau Interport, Balikpapan', 'Pelabuhan PLTU Paiton, Jawa Timur', 'SAILING', NOW() - INTERVAL '2 days', NOW() + INTERVAL '3 days', NULL, 'PT Surveyor Indonesia'),
('SHP-2026-0403', 4, 3, 1, 'GAR 5000', 6450.00, 'Palaran Jetty, Samarinda', 'Pelabuhan Khusus Tuban, Jawa Timur', 'LOADING', NOW() - INTERVAL '12 hours', NOW() + INTERVAL '5 days', NULL, 'PT Geoservices'),
('SHP-2026-0404', 5, 5, 3, 'GAR 4200', 8100.00, 'Trisakti Port, Banjarmasin', 'Jetty Morowali Utara, Sulawesi Tengah', 'SAILING', NOW() - INTERVAL '1 day', NOW() + INTERVAL '4 days', NULL, 'PT Carsurin'),
('SHP-2026-0398', 2, 6, 2, 'GAR 4200', 7950.00, 'Kariangau Interport, Balikpapan', 'Kawasan Industri Bantaeng, Sulawesi Selatan', 'COMPLETED', NOW() - INTERVAL '8 days', NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days', 'PT Surveyor Indonesia');

-- 7. Insert Initial Sample Audit Log
INSERT INTO audit_log (trace_id, session_id, user_id, user_role, user_query, routed_intent, tool_name, tool_arguments, tool_result_summary, execution_status, latency_ms, prompt_tokens, completion_tokens, total_tokens, estimated_cost_usd, pii_masked, guardrail_flagged) VALUES
('trace-init-sample-001', 'sess-001', 'USR-081', 'manager', 'Cek stok batubara GAR 4200 di Palaran', 'sql_query', 'sql_query', '{"query": "SELECT grade, tonnage_mt, temperature_celsius FROM coal_inventory WHERE stockpile_id=1 AND grade=\x27GAR 4200\x27"}'::jsonb, 'Ditemukan 42,500 MT batubara GAR 4200 dengan suhu 39.2 C di Stockpile Palaran', 'SUCCESS', 245.50, 420, 110, 530, 0.000318, false, false);
