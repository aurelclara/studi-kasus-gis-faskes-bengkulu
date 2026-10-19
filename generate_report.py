"""Membuat laporan HTML mandiri (index.html): KPI, peta SVG, grafik, tabel, rekomendasi.
Tidak butuh internet atau pustaka tambahan."""
import math
from html import escape
import analisis_gis as g

W, H, PAD = 640, 520, 24


def peta_svg(d):
    lat0 = g.PUSAT_BENGKULU[0]
    kx = math.cos(math.radians(lat0))
    titik = ([(float(f["lat"]), float(f["lon"])) for f in d["faskes"]] +
             [(float(r["lat"]), float(r["lon"])) for r in d["hasil"]] +
             [(r["lat"], r["lon"]) for r in d["rekom"]])
    la = [t[0] for t in titik]; lo = [t[1] * kx for t in titik]
    skala = min((W - 2 * PAD) / (max(lo) - min(lo)), (H - 2 * PAD) / (max(la) - min(la)))
    X = lambda lon: PAD + (lon * kx - min(lo)) * skala
    Y = lambda lat: H - PAD - (lat - min(la)) * skala
    r_px = g.RADIUS_KM / 111.19 * skala
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Peta aksesibilitas faskes">']
    for f in d["faskes"]:
        s.append(f'<circle cx="{X(float(f["lon"])):.1f}" cy="{Y(float(f["lat"])):.1f}" r="{r_px:.1f}" class="cov"/>')
    for r in d["hasil"]:
        c = "ok" if r["terlayani"] else "bad"
        rad = 3 + int(r["penduduk"]) / 120
        s.append(f'<circle cx="{X(float(r["lon"])):.1f}" cy="{Y(float(r["lat"])):.1f}" r="{rad:.1f}" class="{c}">'
                 f'<title>{r["id"]}: {r["penduduk"]} jiwa, {r["jarak_km"]} km</title></circle>')
    for f in d["faskes"]:
        x, y = X(float(f["lon"])), Y(float(f["lat"]))
        s.append(f'<rect x="{x-6:.1f}" y="{y-6:.1f}" width="12" height="12" class="fas"><title>{escape(f["nama"])}</title></rect>')
    for i, r in enumerate(d["rekom"], 1):
        x, y = X(r["lon"]), Y(r["lat"])
        s.append(f'<text x="{x:.1f}" y="{y+7:.1f}" text-anchor="middle" class="star">&#9733;</text>'
                 f'<text x="{x+14:.1f}" y="{y-6:.1f}" class="lbl">R{i}</text>')
    s.append("</svg>")
    return "".join(s)


def bar_svg(items, fmt, w=420, h=210):
    """items: [(label, nilai 0-100)]"""
    n = len(items); bw = (w - 60) / n
    s = [f'<svg viewBox="0 0 {w} {h}" role="img">']
    for t in (0, 25, 50, 75, 100):
        y = h - 40 - t / 100 * (h - 70)
        s.append(f'<line x1="40" x2="{w-10}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>'
                 f'<text x="34" y="{y+4:.1f}" text-anchor="end" class="ax">{t}%</text>')
    for i, (lab, v) in enumerate(items):
        bh = v / 100 * (h - 70); x = 48 + i * bw
        s.append(f'<rect x="{x:.1f}" y="{h-40-bh:.1f}" width="{bw-14:.1f}" height="{bh:.1f}" class="bar"/>'
                 f'<text x="{x+(bw-14)/2:.1f}" y="{h-44-bh:.1f}" text-anchor="middle" class="val">{fmt(v)}</text>'
                 f'<text x="{x+(bw-14)/2:.1f}" y="{h-20}" text-anchor="middle" class="ax">{lab}</text>')
    s.append("</svg>")
    return "".join(s)


def buat_html(d):
    r = d["ringkasan"]
    chart_rad = bar_svg([(f'{s["radius"]:g} km', s["persen_terlayani"]) for s in d["sens"]],
                        lambda v: f"{v:.1f}%")
    chart_k = bar_svg([("Awal" if c["k"] == 0 else f'+{c["k"]}', c["persen"]) for c in d["kurva"]],
                      lambda v: f"{v:.1f}%")
    terburuk = sorted([x for x in d["hasil"] if not x["terlayani"]],
                      key=lambda x: int(x["penduduk"]) * x["jarak_km"], reverse=True)[:10]
    baris = "".join(f'<tr><td>{x["id"]}</td><td>{x["penduduk"]}</td><td>{x["jarak_km"]}</td>'
                    f'<td>{x["faskes_terdekat"]}</td></tr>' for x in terburuk)
    rek = "".join(f'<li><b>R{i}</b> pada ({x["lat"]:.4f}, {x["lon"]:.4f}) menjangkau tambahan '
                  f'<b>{x["penduduk_baru_terjangkau"]:,}</b> jiwa.</li>' for i, x in enumerate(d["rekom"], 1))
    return f"""<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Studi Kasus GIS: Aksesibilitas Faskes Kota Bengkulu</title>
<style>
:root{{--bg:#f6f7f9;--card:#fff;--tx:#1b1f24;--mut:#5b6573;--ac:#2a7f9e;--ok:#2a9d8f;--bad:#e63946;--gr:#e3e6ea}}
@media (prefers-color-scheme:dark){{:root{{--bg:#14181c;--card:#1d2329;--tx:#e8ebee;--mut:#9aa5b1;--ac:#5bb4d4;--gr:#2c343c}}}}
body{{margin:0;background:var(--bg);color:var(--tx);font:16px/1.55 system-ui,sans-serif}}
main{{max-width:980px;margin:auto;padding:24px 16px 48px}}
h1{{font-size:1.7rem;margin:.2em 0}} h2{{margin-top:1.6em;border-bottom:2px solid var(--ac);padding-bottom:4px}}
.sub{{color:var(--mut)}} .kpi{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:18px 0}}
.k{{background:var(--card);border-radius:10px;padding:14px;box-shadow:0 1px 4px #0002}}
.k b{{display:block;font-size:1.8rem;color:var(--ac)}} .k span{{color:var(--mut);font-size:.9rem}}
.card{{background:var(--card);border-radius:10px;padding:14px;box-shadow:0 1px 4px #0002;overflow-x:auto}}
.two{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}}
table{{border-collapse:collapse;width:100%}} td,th{{padding:6px 10px;border-bottom:1px solid var(--gr);text-align:left;vertical-align:top}}
svg{{width:100%;height:auto}} .cov{{fill:var(--ok);fill-opacity:.08;stroke:var(--ok);stroke-width:1}}
.ok{{fill:var(--ok);fill-opacity:.75}} .bad{{fill:var(--bad);fill-opacity:.75}} .fas{{fill:var(--ac)}}
.star{{font-size:22px;fill:#f4a261;stroke:#000;stroke-width:.4}} .lbl{{font-size:12px;fill:var(--tx);font-weight:700}}
.grid{{stroke:var(--gr)}} .ax{{font-size:11px;fill:var(--mut)}} .val{{font-size:11px;fill:var(--tx);font-weight:700}} .bar{{fill:var(--ac)}}
.lg span{{display:inline-block;margin-right:14px;font-size:.9rem}}
</style></head><body><main>
<h1>Aksesibilitas Fasilitas Kesehatan dengan GIS</h1>
<p class="sub">Studi kasus CRISP-DM dari kuliah praktisi <i>Career and Competition in Industrial Era with GIS</i>
(Widi Primadepa, GIS Analyst). Data <b>sintetis</b> di sekitar Kota Bengkulu, untuk pembelajaran.</p>
<div class="kpi">
<div class="k"><b>{r["persen_terlayani"]}%</b><span>penduduk terlayani (radius {g.RADIUS_KM:g} km)</span></div>
<div class="k"><b>{r["penduduk_terlayani"]:,}</b><span>dari {r["total_penduduk"]:,} jiwa</span></div>
<div class="k"><b>{r["permukiman_tidak_terlayani"]}</b><span>permukiman di luar jangkauan</span></div>
<div class="k"><b>{d["kurva"][-1]["persen"]}%</b><span>cakupan setelah {len(d["rekom"])} fasilitas baru</span></div></div>

<h2>1. Business Understanding</h2>
<p>Perencanaan pembangunan membutuhkan jawaban atas dua pertanyaan: seberapa banyak penduduk yang berada
dalam jangkauan layanan kesehatan, dan di mana fasilitas baru paling efektif dibangun. Lulusan Informatika dapat
mengotomatiskan analisis ini, bukan sekadar menggambar peta secara manual.</p>

<h2>2. Data Understanding &amp; Preparation</h2>
<p>{len(d["faskes"])} fasilitas dan {len(d["hasil"])} titik permukiman (atribut: koordinat, jumlah penduduk), dibuat dengan
<code>seed</code> tetap. Tahap validasi membuang baris dengan koordinat atau atribut tidak valid.</p>

<h2>3. Modeling</h2>
<p>Jarak Haversine ke fasilitas terdekat, penentuan status <i>terlayani</i> (jarak &le; {g.RADIUS_KM:g} km), lalu
rekomendasi lokasi dengan <i>greedy maximum coverage</i>.</p>
<div class="card"><div class="lg"><span style="color:var(--ok)">&#9679; terlayani</span>
<span style="color:var(--bad)">&#9679; tidak terlayani</span><span style="color:var(--ac)">&#9632; faskes</span>
<span style="color:#f4a261">&#9733; lokasi rekomendasi</span></div>{peta_svg(d)}</div>

<h2>4. Evaluation</h2>
<div class="two"><div class="card"><b>Sensitivitas radius layanan</b>{chart_rad}</div>
<div class="card"><b>Cakupan setelah menambah fasilitas</b>{chart_k}</div></div>
<p>Hasil sangat dipengaruhi asumsi radius, sehingga angka perlu dibaca bersama analisis sensitivitas.
Perhitungan jarak dan cakupan diverifikasi dengan pengujian otomatis (<code>tests/</code>).</p>

<h2>5. Deployment &amp; Rekomendasi</h2>
<ul>{rek}</ul>
<div class="card"><b>10 permukiman prioritas (penduduk &times; jarak terbesar)</b>
<table><tr><th>ID</th><th>Penduduk</th><th>Jarak (km)</th><th>Faskes terdekat</th></tr>{baris}</table></div>

<h2>Keterbatasan</h2>
<p>Jarak garis lurus (bukan jarak tempuh jalan), kapasitas fasilitas tidak dihitung, dan data bukan data resmi.
Pengembangan: data OSM/BPS/Dinkes, routing jaringan jalan (pgRouting/OSRM), dan basis data PostGIS (<code>sql/</code>).</p>
</main></body></html>"""


if __name__ == "__main__":
    data = g.run(verbose=False)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(buat_html(data))
    print("index.html dibuat.")
