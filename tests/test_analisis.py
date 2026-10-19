"""Pengujian: hasil perhitungan (termasuk kode yang dibantu AI) harus diverifikasi."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import analisis_gis as g


def test_haversine_nol():
    assert g.haversine_km(-3.8, 102.26, -3.8, 102.26) == 0


def test_haversine_satu_derajat_lintang():
    assert abs(g.haversine_km(0, 0, 1, 0) - 111.19) < 0.5


def test_validate_membuang_data_buruk():
    rows = [{"id": "1", "lat": "-3.8", "lon": "102.2"}, {"id": "2", "lat": "abc", "lon": "102.2"},
            {"id": "3", "lat": "95", "lon": "102.2"}, {"id": "", "lat": "-3.8", "lon": "102.2"}]
    valid, ditolak = g.validate(rows, ["id", "lat", "lon"])
    assert len(valid) == 1 and len(ditolak) == 3


def test_nearest_dan_coverage():
    faskes = [{"id": "F1", "nama": "A", "lat": "0", "lon": "0"}]
    perm = [{"id": "P1", "lat": "0", "lon": "0.01", "penduduk": "100"},
            {"id": "P2", "lat": "0", "lon": "0.10", "penduduk": "300"}]
    hasil = g.nearest_facility(perm, faskes)
    assert hasil[0]["terlayani"] and not hasil[1]["terlayani"]
    assert g.coverage_summary(hasil)["persen_terlayani"] == 25.0


def test_rekomendasi():
    faskes = [{"id": "F1", "nama": "A", "lat": "0", "lon": "0"}]
    perm = [{"id": "P1", "lat": "0", "lon": "0.10", "penduduk": "300"},
            {"id": "P2", "lat": "0", "lon": "0.101", "penduduk": "200"}]
    rekom = g.recommend_sites(g.nearest_facility(perm, faskes), k=1)
    assert rekom[0]["penduduk_baru_terjangkau"] == 500


def test_sensitivitas_naik_dengan_radius():
    faskes = [{"id": "F1", "nama": "A", "lat": "0", "lon": "0"}]
    perm = [{"id": "P1", "lat": "0", "lon": "0.02", "penduduk": "100"},
            {"id": "P2", "lat": "0", "lon": "0.05", "penduduk": "100"}]
    p = [s["persen_terlayani"] for s in g.sensitivity_radius(perm, faskes, [1, 3, 6])]
    assert p == sorted(p) and p[-1] == 100.0
