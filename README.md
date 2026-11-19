# AI Excel Copilot

## Backend
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add OPENAI_API_KEY (or set MOCK_LLM=1 to try offline)
uvicorn app.main:app --reload --port 8000

## Frontend
cd frontend
npm install
npm run dev                 # http://localhost:5173

## Deploy
Render: root=backend, start=`gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker`, env OPENAI_API_KEY, ALLOWED_ORIGINS=<your Vercel URL>
Vercel: root=frontend, env VITE_API_URL=https://<backend>.onrender.com/api/ask
