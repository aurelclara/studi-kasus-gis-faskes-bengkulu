# Analisis Aksesibilitas Fasilitas Kesehatan dengan GIS

Studi kasus **CRISP-DM** berdasarkan kuliah praktisi *Career and Competition in Industrial Era with GIS*
(Widi Primadepa, GIS Analyst, City Care Property, Christchurch; Informatics Practitioner Lecture Series,
Program Studi Informatika Universitas Bengkulu). Proyek ini menunjukkan bagaimana latar belakang IT
(pemrograman, otomasi, dan integrasi data) dapat dipakai untuk menjawab masalah perencanaan pembangunan di Kota Bengkulu.

🔗 Laporan HTML (live, setelah GitHub Pages aktif):
`https://USERNAME.github.io/studi-kasus-gis-faskes-bengkulu/`

## Kerangka CRISP-DM

| Tahap | Penjelasan |
|---|---|
| **Business Understanding** | Perencana perlu tahu berapa penduduk yang berada dalam jangkauan layanan kesehatan dan di mana fasilitas baru paling efektif dibangun. Analisis diotomatisasi agar dapat diulang saat data berubah. |
| **Data Understanding & Preparation** | 10 fasilitas dan 150 titik permukiman (koordinat, jumlah penduduk), data sintetis dengan `seed` tetap, plus tahap validasi koordinat dan atribut. |
| **Modeling** | Jarak Haversine ke fasilitas terdekat, status terlayani (radius 2 km), dan rekomendasi lokasi baru dengan *greedy maximum coverage*. |
| **Evaluation** | Analisis sensitivitas radius (1 sampai 4 km), kurva cakupan setelah penambahan fasilitas, dan pengujian otomatis perhitungan. |
| **Deployment** | Laporan HTML berisi KPI, peta, grafik, tabel prioritas, dan rekomendasi, serta output CSV/GeoJSON untuk dibuka di QGIS/ArcGIS. |

## Keterkaitan dengan Materi

| Poin materi | Implementasi |
|---|---|
| IT sebagai keunggulan: membuat alat dan mengotomatisasi alur kerja | Seluruh analisis berjalan dengan satu perintah |
| Python, SQL, dan PostGIS | `analisis_gis.py` dan `sql/postgis_queries.sql` |
| Data tersebar dan standar berbeda | Tahap validasi data |
| AI sebagai alat bantu, hasil harus diperiksa | `tests/test_analisis.py` |
| Portofolio dan pengalaman praktis | Repositori ini |

## Hasil Ringkas (data sintetis)

- Penduduk terlayani radius 2 km: **46,76%** (20.119 dari 43.023 jiwa).
- Sensitivitas: 14,37% (1 km), 70,69% (3 km), 88,35% (4 km). Hasil sangat bergantung pada asumsi radius.
- Tiga fasilitas baru yang direkomendasikan menaikkan cakupan menjadi **84,5%**.

## Struktur Proyek

```
studi-kasus-gis-faskes-bengkulu/
├── analisis_gis.py       # Analisis CRISP-DM (hasil di terminal + folder output/)
├── generate_report.py    # Pembuat laporan HTML
├── index.html            # Laporan visual (buka di browser, tanpa internet)
├── data/                 # faskes.csv, permukiman.csv (sintetis)
├── output/               # hasil_analisis.csv, permukiman_hasil.geojson, ringkasan.json
├── sql/postgis_queries.sql
├── tests/test_analisis.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Cara Menjalankan

```bash
git clone https://github.com/USERNAME/studi-kasus-gis-faskes-bengkulu.git
cd studi-kasus-gis-faskes-bengkulu

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt  # hanya pytest (opsional)

python analisis_gis.py           # analisis di terminal + output/
python generate_report.py        # membuat ulang index.html
pytest -q                        # pengujian
```

## Laporan HTML

- **Membuka lokal:** double-click `index.html` (peta dan grafik sudah tertanam, tanpa server).
- **Lewat link:** aktifkan GitHub Pages di **Settings → Pages**, pilih branch `main` dan folder `/ (root)`.

## Catatan

Data adalah **simulasi** untuk pembelajaran, bukan data resmi. Jarak memakai garis lurus (bukan jarak tempuh jalan)
dan kapasitas fasilitas belum diperhitungkan. Untuk analisis nyata, ganti isi `data/*.csv` dengan data BPS, BIG,
Dinkes, atau OpenStreetMap berformat kolom sama.

## Lisensi

Kuliah praktisi Informatics Practitioner Lecture Series 2026, Widi Primadepa. 
