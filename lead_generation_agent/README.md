# Lead Generation Agent (Flask + SQLite)

This project is a modular, beginner-friendly lead generation system.

## Folder Structure

```text
lead_generation_agent/
│
├── app.py
├── requirements.txt
│
├── config/
│   └── settings.py
│
├── models/
│   └── lead.py
│
├── routes/
│   └── leads.py
│
├── services/
│   ├── validation.py
│   ├── enrichment.py
│   ├── storage.py
│   └── automation.py
│
├── templates/
│   └── dashboard.html
│
├── static/
│   └── style.css
│
├── utils/
│   ├── logger.py
│   └── csv_export.py
│
└── data/
    ├── leads.db
    └── sample_leads.csv
```

## Run Instructions

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start app:
   ```bash
   python app.py
   ```
3. Open dashboard: `http://localhost:5000`
4. Use REST APIs at the same host.

## Optional Manual CLI Mode

```bash
python app.py --manual
```

## API Endpoints

- `POST /leads`
- `GET /leads`
- `GET /leads/search`
- `DELETE /leads/{id}`
- `GET /leads/export`
- `GET /health`

## Preview Of This Project

- Dashboard includes:
  - web lead form
  - CSV upload form
  - status filter
  - lead table
  - one-click CSV export
- API supports full lead lifecycle (create, list, search, delete, export).

## Data Flow (High-Level)

1. Input comes from web form, CSV upload, API, or CLI.
2. Validation checks required fields, email, and phone.
3. Duplicate check uses unique email in database.
4. Enrichment computes domain/category/score/country.
5. Automation sets status and simulates next action.
6. Lead is stored in SQLite and visible on dashboard/API.
