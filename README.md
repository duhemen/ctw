<!-- CTW README -->
<div align="center">

```
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║      ██████╗████████╗██╗    ██╗                                          ║
║     ██╔════╝╚══██╔══╝██║    ██║                                          ║
║     ██║        ██║   ██║ █╗ ██║                                          ║
║     ██║        ██║   ██║███╗██║                                          ║
║     ╚██████╗   ██║   ╚███╔███╔╝                                          ║
║      ╚═════╝   ╚═╝    ╚══╝╚══╝                                           ║
║                                                                          ║
║        Construction Transparency Watch                                   ║
║        ───────────────────────────────                                   ║
║        Pengawasan Konstruksi Berbasis Geospasial                         ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9-199900?style=for-the-badge&logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

<p align="center"><strong>Platform pengawasan konstruksi berbasis geospasial</strong> yang transparan, partisipatif, dan terdesentralisasi.<br>
Masyarakat dapat memantau proyek konstruksi di wilayahnya, melihat progress real-time, dan melaporkan temuan lapangan.</p>

<sub>📅 Build: 23 September 2026 • 🚀 Status: Development</sub>

</div>

---

## 🌟 Fitur Utama

| Kategori | Fitur |
|---|---|
| 🗺️ **Geospasial** | Peta Leaflet, batas wilayah 4 level, 91.162 wilayah Indonesia |
| 📊 **Transparansi** | Progress fisik & keuangan, kurva S, milestone, galeri foto |
| 📣 **Partisipatif** | Feedback 3 pilar (Audit, Inspeksi, Laporan Publik) |
| ⛔ **Anti-Korupsi** | Daftar hitam penyedia, alasan & dasar hukum |
| 🔒 **Keamanan** | Rate limiting, CSRF, session auth (PBKDF2) |
| 🎨 **UI/UX** | Toast, skeleton, animasi, print-friendly, mobile responsive |

---

## 🚀 Instalasi

### Prasyarat
- **Python** 3.10+
- **Anaconda/Miniconda**
- **Git**

### Langkah Cepat

```bash
# 1. Clone repository
git clone https://github.com/duhemen/ctw.git
cd ctw

# 2. Buat environment
conda env create -f environment.yml
conda activate ctw_env

# 3. Setup environment
cp .env.example .env
# Generate: python -c "import secrets; print(secrets.token_urlsafe(64))"

# 4. Inisialisasi database
python scripts/init_db.py
python scripts/import_wilayah.py
python scripts/import_observations.py
python scripts/init_admin.py

# 5. Jalankan
uvicorn server.main:app --reload --port 8000
```

**Akses:**

| URL | Fungsi |
|---|---|
| http://127.0.0.1:8000/ | Dashboard publik |
| http://127.0.0.1:8000/admin/login | Admin panel |
| http://127.0.0.1:8000/admin/docs | API docs (login required) |

Default login: **`admin`** / **`admin123`** ← *Ganti setelah login pertama!*

---

## 🏗️ Arsitektur

```
ctw/
├── core/                    # Business logic
│   ├── models.py            # SQLAlchemy models
│   ├── database.py          # DB connection
│   ├── auth.py              # Auth helpers
│   ├── csrf.py              # CSRF protection
│   └── rate_limit.py        # Rate limiting
│
├── server/                  # FastAPI backend
│   ├── main.py              # App entry point
│   ├── api/routes/          # REST API endpoints
│   ├── templates/           # Jinja2 HTML
│   └── static/              # CSS, JS
│
├── scripts/                 # Utility scripts
├── data/                    # Local data (gitignored)
├── config.py                # Environment config
└── environment.yml          # Conda environment
```

---

## 📡 API Endpoints

### Public API

| Method | Endpoint | Deskripsi |
|---|---|---|
| `GET` | `/api/regions` | Daftar wilayah |
| `GET` | `/api/regions/search` | Cari wilayah by nama |
| `GET` | `/api/regions/{code}/geojson` | Batas wilayah GeoJSON |
| `GET` | `/api/dashboard` | Statistik dashboard |
| `GET` | `/api/projects/{id}/detail` | Detail proyek |
| `GET` | `/api/providers` | Daftar penyedia |
| `GET` | `/api/blacklist` | Daftar hitam |
| `GET` | `/api/observations` | Observasi lapangan |

### Admin API

| Method | Endpoint | Deskripsi |
|---|---|---|
| `POST` | `/admin/login` | Login |
| `GET/POST` | `/admin/projects/*` | CRUD proyek |
| `GET/POST` | `/admin/providers/*` | CRUD penyedia |
| `GET/POST` | `/admin/blacklist/*` | CRUD blacklist |
| `POST` | `/admin/projects/{id}/photos/upload` | Upload foto |

---

## 🛠️ Tech Stack

| Layer | Teknologi |
|---|---|
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **Database** | SQLite (dev), PostgreSQL (production-ready) |
| **ORM** | SQLAlchemy 2.0 |
| **Geospasial** | GeoPandas, Shapely, Leaflet.js |
| **Frontend** | Jinja2, Vanilla JS, Chart.js |
| **Auth** | Session-based, PBKDF2 |
| **Security** | CSRF, Rate limiting (slowapi) |

---

## 🎯 Roadmap

- [x] Fase 1 — Fondasi Dashboard + Wilayah
- [x] Fase 2A — Filter Wilayah + Popup Detail
- [x] Fase 2B — Admin Panel (CRUD)
- [x] Fase 2C — Upload Foto
- [x] Security — CSRF + Rate Limiting
- [x] UI/UX Polish — Toast, Skeleton, Animation
- [x] Fase C1 — Observasi Lapangan
- [ ] Fase C2 — Integrasi `peatfr` (Prediksi Risiko Gambut)
- [ ] Fase C3 — Cross-reference Observasi ↔ Proyek
- [ ] Fase C4 — Dashboard Analitik Spasial-Ekonomi
- [ ] Fase B — Cloudflare Tunnel Deploy
- [ ] Fase D — Client Desktop PyQt

---

## 🌐 Desentralisasi

CTW dirancang **terdesentralisasi**:
- Setiap organisasi bisa host instance sendiri
- Tidak ada server pusat — data di tangan pemiliknya
- Deploy mudah via **Cloudflare Tunnel** (tanpa VPS)

---

## 🤝 Kontribusi

1. Fork repository
2. Buat branch: `git checkout -b feature/NamaFitur`
3. Commit: `git commit -am 'Add: fitur baru'`
4. Push: `git push origin feature/NamaFitur`
5. Buka Pull Request

---

## 📄 Lisensi

MIT License — bebas digunakan, dimodifikasi, dan didistribusikan dengan atribusi.

---

## 🙏 Kredit

- [cahyadsn/wilayah_boundaries](https://github.com/cahyadsn/wilayah_boundaries)
- [mellygsIn/peatfr](https://github.com/mellygsIn/peatfr)
- OpenStreetMap contributors

---

<div align="center">

**Construction Transparency Watch** — *Karena transparansi adalah fondasi kepercayaan publik.*

Made with ❤️ in Indonesia 🇮🇩

</div>
