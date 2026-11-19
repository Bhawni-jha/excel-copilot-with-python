# Sheetwise

Sheetwise lets you upload an Excel or CSV file, ask questions in plain English, and get data-backed tables and charts. Suggested questions are generated from the columns and values in the uploaded file.

## Features

- Supports `.xlsx`, `.xls`, and `.csv` files
- Dynamic questions based on the uploaded file
- Totals, averages, rankings, grouping, and text filters
- Result tables, charts, and generated Python code
- Offline demo mode with `MOCK_LLM=1`

## Run locally

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `MOCK_LLM=1` in `.env` for offline use, or add an API key for AI-generated analysis.

```powershell
uvicorn app.main:app --reload --port 8000
```

The API runs at `http://localhost:8000`.

### Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

## Production

For Render, use `backend` as the root directory and:

```text
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

For Vercel, use `frontend` as the root directory and set:

```text
VITE_API_URL=https://<your-backend>/api/ask
```
