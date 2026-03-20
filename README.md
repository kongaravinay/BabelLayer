# BabelLayer

**BabelLayer** handles the boring work of mapping data between different formats and schemas. It's for anyone who's ever had to manually rename columns in Excel or write scripts to move data from one dataset to another.

### What it does:
- **Field Matching**: Automatically guesses column mappings.
- **Transformation**: Moves data between CSV, JSON, XML, or Excel.
- **Data Quality**: Flags missing values or weird anomalies.
- **PDF Reports**: Quick summaries of what's in your data.

---

### How to use it:

1.  **Clone it**: `git clone https://github.com/kongaravinay/BabelLayer.git`
2.  **Environment**: `python -m venv .venv` and activate it.
3.  **Install**: `pip install -r requirements.txt`
4.  **Database**: `python src/database/init_db.py`
5.  **Run**: `python src/main.py`

---

### Why this exists:
I built this because I got tired of manually mapping fields across files. It's meant to be a simple tool that actually saves time.

- [Check the TODO list](docs/TODO.md) for what's coming next.
- [License is MIT](LICENSE).

---
**Author: Kongara Vinay**
[Project GitHub](https://github.com/kongaravinay/BabelLayer)