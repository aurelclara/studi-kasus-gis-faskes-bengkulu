"""
Analisis aksesibilitas fasilitas kesehatan (GIS) dengan alur CRISP-DM.
Hanya memakai pustaka standar Python.

Jalankan:  python analisis_gis.py
"""
import csv
import json
import math
import random
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
OUT_DIR = BASE / "output"

PUSAT_BENGKULU = (-3.80, 102.26)   # (lat, lon) perkiraan pusat Kota Bengkulu
RADIUS_KM = 2.0                    # ambang jarak layanan (asumsi)
RADIUS_SENSITIVITAS = [1.0, 1.5, 2.0, 3.0, 4.0]
K_REKOMENDASI = 3


# ---------- Data Understanding & Preparation ----------
def generate_data(seed=42, n_faskes=10, n_permukiman=150):
    """Data sintetis (seed tetap). Ganti dengan data resmi untuk analisis nyata."""
    rng = random.Random(seed)
    lat0, lon0 = PUSAT_BENGKULU
    DATA_DIR.mkdir(exist_ok=True)
    with open(DATA_DIR / "faskes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "nama", "lat", "lon"])
        for i in range(1, n_faskes + 1):
            w.writerow([f"F{i:02d}", f"Puskesmas Contoh {i}",
                        round(lat0 + rng.uniform(-0.05, 0.05), 6),
                        round(lon0 + rng.uniform(-0.05, 0.05), 6)])
    klaster = [(lat0 + rng.uniform(-0.06, 0.06), lon0 + rng.uniform(-0.06, 0.06))
               for _ in range(6)]
    with open(DATA_DIR / "permukiman.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "lat", "lon", "penduduk"])
        for i in range(1, n_permukiman + 1):
            c = rng.choice(klaster)
            w.writerow([f"P{i:03d}", round(c[0] + rng.gauss(0, 0.012), 6),
                        round(c[1] + rng.gauss(0, 0.012), 6), rng.randint(50, 500)])


def load_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validate(rows, kolom):
    """Membuang baris dengan atribut kosong atau koordinat di luar rentang."""
    valid, ditolak = [], []
    for r in rows:
        try:
            lat, lon = float(r["lat"]), float(r["lon"])
            ok = all(r.get(k) not in (None, "") for k in kolom)
            ok = ok and -90 <= lat <= 90 and -180 <= lon <= 180
        except (ValueError, KeyError):
            ok = False
        (valid if ok else ditolak).append(r)
    return valid, ditolak


# ---------- Modeling ----------
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def nearest_facility(permukiman, faskes, radius=RADIUS_KM):
    hasil = []
    for p in permukiman:
        plat, plon = float(p["lat"]), float(p["lon"])
        jarak, id_f = min((haversine_km(plat, plon, float(f["lat"]), float(f["lon"])), f["id"])
                          for f in faskes)
        hasil.append({**p, "faskes_terdekat": id_f, "jarak_km": round(jarak, 3),
                      "terlayani": jarak <= radius})
    return hasil


def coverage_summary(hasil):
    total = sum(int(r["penduduk"]) for r in hasil)
    ok = sum(int(r["penduduk"]) for r in hasil if r["terlayani"])
    return {"total_penduduk": total, "penduduk_terlayani": ok,
            "persen_terlayani": round(100 * ok / total, 2) if total else 0.0,
            "permukiman_tidak_terlayani": sum(not r["terlayani"] for r in hasil)}


def recommend_sites(hasil, k=K_REKOMENDASI, radius=RADIUS_KM):
    """Greedy maximum coverage: pilih kandidat yang menjangkau penduduk
    tidak terlayani terbanyak, ulangi k kali."""
    belum = [r for r in hasil if not r["terlayani"]]
    kandidat = list(belum)
    rekom = []
    for _ in range(k):
        if not belum or not kandidat:
            break
        best, skor_best, dij_best = None, 0, []
        for c in kandidat:
            dij = [r for r in belum if haversine_km(
                float(c["lat"]), float(c["lon"]), float(r["lat"]), float(r["lon"])) <= radius]
            skor = sum(int(r["penduduk"]) for r in dij)
            if skor > skor_best:
                best, skor_best, dij_best = c, skor, dij
        if best is None:
            break
        rekom.append({"lat": float(best["lat"]), "lon": float(best["lon"]),
                      "penduduk_baru_terjangkau": skor_best})
        ids = {r["id"] for r in dij_best}
        belum = [r for r in belum if r["id"] not in ids]
    return rekom


# ---------- Evaluation ----------
def sensitivity_radius(perm, faskes, radii=RADIUS_SENSITIVITAS):
    """Persentase penduduk terlayani untuk beberapa radius layanan."""
    return [{"radius": r, **coverage_summary(nearest_facility(perm, faskes, r))} for r in radii]


def coverage_vs_new_sites(ringkasan, rekom):
    """Cakupan kumulatif setelah menambah 0..k fasilitas baru."""
    total, ok = ringkasan["total_penduduk"], ringkasan["penduduk_terlayani"]
    kurva = [{"k": 0, "persen": round(100 * ok / total, 2)}]
    for i, r in enumerate(rekom, 1):
        ok += r["penduduk_baru_terjangkau"]
        kurva.append({"k": i, "persen": round(100 * ok / total, 2)})
    return kurva


# ---------- Deployment (data keluaran) ----------
def save_outputs(hasil, ringkasan, rekom):
    OUT_DIR.mkdir(exist_ok=True)
    with open(OUT_DIR / "hasil_analisis.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(hasil[0].keys()))
        w.writeheader()
        w.writerows(hasil)
    fitur = [{"type": "Feature",
              "geometry": {"type": "Point", "coordinates": [float(r["lon"]), float(r["lat"])]},
              "properties": {k: v for k, v in r.items() if k not in ("lat", "lon")}}
             for r in hasil]
    (OUT_DIR / "permukiman_hasil.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": fitur}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    (OUT_DIR / "ringkasan.json").write_text(
        json.dumps({"ringkasan": ringkasan, "rekomendasi": rekom}, indent=2), encoding="utf-8")


def run(verbose=True):
    if not (DATA_DIR / "faskes.csv").exists():
        generate_data()
    faskes, tf = validate(load_csv(DATA_DIR / "faskes.csv"), ["id", "nama", "lat", "lon"])
    perm, tp = validate(load_csv(DATA_DIR / "permukiman.csv"), ["id", "lat", "lon", "penduduk"])
    hasil = nearest_facility(perm, faskes)
    ringkasan = coverage_summary(hasil)
    rekom = recommend_sites(hasil)
    sens = sensitivity_radius(perm, faskes)
    kurva = coverage_vs_new_sites(ringkasan, rekom)
    save_outputs(hasil, ringkasan, rekom)
    if verbose:
        print("=== CRISP-DM: Aksesibilitas Fasilitas Kesehatan, Kota Bengkulu ===")
        print(f"[Data] {len(faskes)} faskes, {len(perm)} permukiman (baris ditolak: {len(tf)+len(tp)})")
        print(f"[Modeling] radius layanan {RADIUS_KM} km")
        print(f"  Penduduk terlayani : {ringkasan['persen_terlayani']}% "
              f"({ringkasan['penduduk_terlayani']:,} / {ringkasan['total_penduduk']:,})")
        print(f"  Permukiman di luar jangkauan: {ringkasan['permukiman_tidak_terlayani']}")
        for i, r in enumerate(rekom, 1):
            print(f"  Rekomendasi {i}: ({r['lat']:.5f}, {r['lon']:.5f}) +{r['penduduk_baru_terjangkau']:,} jiwa")
        print("[Evaluation] sensitivitas radius:")
        for s in sens:
            print(f"  {s['radius']:>4} km -> {s['persen_terlayani']}%")
        print("  cakupan setelah tambah fasilitas:",
              ", ".join(f"+{c['k']}: {c['persen']}%" for c in kurva))
        print("[Deployment] output/ dan index.html (jalankan generate_report.py)")
    return {"faskes": faskes, "hasil": hasil, "ringkasan": ringkasan,
            "rekom": rekom, "sens": sens, "kurva": kurva}


if __name__ == "__main__":
    run()
