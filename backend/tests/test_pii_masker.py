import pytest
from app.guardrails.pii_masker import PIIMasker


def test_nik_masking():
    masker = PIIMasker()
    raw = "Karyawan atas nama Joko dengan NIK 3174051203890001 bertugas di Jetty Palaran."
    masked, count = masker.mask_text(raw)
    assert count == 1
    assert "317405******0001" in masked
    assert "3174051203890001" not in masked


def test_phone_number_masking():
    masker = PIIMasker()
    # Test standard Indonesian mobile phone
    raw1 = "PIC Bambang Sudiro dapat dihubungi di nomor 081299882341 untuk koordinasi."
    masked1, c1 = masker.mask_text(raw1)
    assert c1 == 1
    assert "0812****2341" in masked1
    assert "081299882341" not in masked1

    # Test +62 international format
    raw2 = "Kontak darurat: +6281388771122 standby 24 jam."
    masked2, c2 = masker.mask_text(raw2)
    assert c2 == 1
    assert "+62813****1122" in masked2


def test_email_masking():
    masker = PIIMasker()
    raw = "Kirim invoice resmi ke alamat bambang.sudiro@plnepi.co.id segera."
    masked, count = masker.mask_text(raw)
    assert count == 1
    assert "bam***@plnepi.co.id" in masked
    assert "bambang.sudiro@plnepi.co.id" not in masked


def test_scan_and_mask_summary():
    masker = PIIMasker()
    raw = "Customer PLN: NIK 3174051203890001, HP 081299882341, Email pic@pln.co.id"
    res = masker.scan_and_mask(raw)
    assert res.is_safe is True
    assert res.masked_items_count == 3
    assert res.violation_type == "PII_DETECTED"
