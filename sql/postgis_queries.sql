-- Padanan analisis di PostGIS (untuk skala data besar / basis data spasial).
-- Prasyarat: CREATE EXTENSION postgis;

CREATE TABLE faskes (
  id text PRIMARY KEY, nama text,
  geom geometry(Point, 4326)
);
CREATE TABLE permukiman (
  id text PRIMARY KEY, penduduk int,
  geom geometry(Point, 4326)
);
CREATE INDEX ON faskes USING gist (geom);
CREATE INDEX ON permukiman USING gist (geom);

-- Jarak ke faskes terdekat (meter): operator KNN <-> untuk mencari kandidat, lalu geography untuk jarak akurat
SELECT p.id, p.penduduk, f.id AS faskes_terdekat,
       ST_Distance(p.geom::geography, f.geom::geography) AS jarak_m
FROM permukiman p
CROSS JOIN LATERAL (
  SELECT id, geom FROM faskes ORDER BY geom <-> p.geom LIMIT 1
) f;

-- Persentase penduduk terlayani pada radius 2 km
SELECT round(100.0 * SUM(p.penduduk) FILTER (WHERE EXISTS (
         SELECT 1 FROM faskes f
         WHERE ST_DWithin(p.geom::geography, f.geom::geography, 2000)))
       / SUM(p.penduduk), 2) AS persen_terlayani
FROM permukiman p;
