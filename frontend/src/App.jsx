import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000/api/ask";
const API_ROOT = API.replace(/\/ask\/?$/, "");
const DEFAULT_SUGGESTIONS = ["How many rows are there?", "Show the columns in this file"];

export default function App() {
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [showCode, setShowCode] = useState(false);
  const [suggestions, setSuggestions] = useState(DEFAULT_SUGGESTIONS);

  const onDrop = useCallback(async (f) => {
    if (!f[0]) return;
    setFile(f[0]);
    setResult(null);
    setSuggestions(DEFAULT_SUGGESTIONS);
    const fd = new FormData();
    fd.append("file", f[0]);
    try {
      const res = await fetch(`${API_ROOT}/suggestions`, { method: "POST", body: fd });
      const data = await res.json();
      if (!data.error && data.suggestions?.length) setSuggestions(data.suggestions);
    } catch {
      // The answer request will show the connection error if the backend is unavailable.
    }
  }, []);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, multiple: false,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    },
  });

  async function ask(e) {
    e.preventDefault();
    if (!file || !question.trim()) return;
    setLoading(true); setResult(null);
    const fd = new FormData();
    fd.append("file", file); fd.append("question", question);
    try {
      const res = await fetch(API, { method: "POST", body: fd });
      const data = await res.json();
      setResult(data);
      if (data.suggestions?.length) setSuggestions(data.suggestions);
    } catch {
      setResult({ error: "Can't reach the server. Check that the backend is running and VITE_API_URL is correct." });
    } finally { setLoading(false); }
  }

  const rows = result?.rows || [];
  const cols = result?.columns || [];
  const yIdx = rows.length ? rows[0].findIndex((v) => typeof v === "number") : -1;
  const xIdx = rows.length ? Math.max(0, rows[0].findIndex((v) => typeof v === "string")) : 0;
  const chartData = yIdx >= 0 ? rows.map((r) => ({ x: String(r[xIdx] ?? ""), y: r[yIdx] })) : [];

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand"><span className="brand-mark">✦</span><span>Sheetwise</span></div>
        <span className="topbar-note">AI spreadsheet insights</span>
      </header>

      <section className="hero">
        <div>
          <div className="eyebrow"><span className="eyebrow-dot" /> YOUR DATA, SIMPLIFIED</div>
          <h1>Ask your spreadsheet<br /><em>anything.</em></h1>
          <p className="hero-copy">Upload your Excel or CSV file and get clear answers, useful summaries and visual insights in seconds.</p>
        </div>
        <div className="hero-stat"><strong>01</strong><span>Upload<br />your file</span></div>
      </section>

      <section {...getRootProps()} className={`upload-card ${isDragActive ? "is-dragging" : ""}`}>
        <input {...getInputProps()} aria-label="Upload spreadsheet" />
        <div className="upload-icon">↑</div>
        {file ? (
          <div>
            <p className="upload-title">{file.name}</p>
            <p className="upload-subtitle">{(file.size / 1024).toFixed(1)} KB · Ready to analyse · Drop another file to replace</p>
          </div>
        ) : (
          <div>
            <p className="upload-title">{isDragActive ? "Drop it here" : "Drop your spreadsheet here"}</p>
            <p className="upload-subtitle">or click to browse · .xlsx, .xls and .csv supported</p>
          </div>
        )}
      </section>

      <section className="question-card">
        <div className="section-label"><span>02</span> ASK A QUESTION</div>
        <form onSubmit={ask}>
          <div className="question-row">
            <input id="q" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="e.g. What were the top 5 selling products?" />
            <button disabled={!file || !question.trim() || loading} className="ask-button">
              {loading ? <><span className="spinner" /> Working</> : <>Get answer <span>→</span></>}
            </button>
          </div>
        </form>
        <div className="suggestion-heading">TRY ASKING</div>
        <div className="suggestions">
          {suggestions.map((ex) => (
            <button type="button" key={ex} onClick={() => setQuestion(ex)} className="suggestion-chip">{ex}<span>↗</span></button>
          ))}
        </div>
      </section>

      {loading && <div role="status" className="status-card"><span className="spinner dark" /> Reading your file and preparing your answer…</div>}
      {result?.error && <div role="alert" className="error-card"><strong>We couldn't answer that.</strong><span>{result.error}</span></div>}

      {result && !result.error && (
        <section className="results-section">
          <div className="results-heading">
            <div><div className="section-label"><span>03</span> YOUR ANSWER</div><h2>Analysis complete</h2></div>
            <div className="result-count"><strong>{result.row_count}</strong><span>{result.row_count === 1 ? "row returned" : "rows returned"}</span></div>
          </div>
          {chartData.length > 0 && (
            <div className="chart-card" aria-label="Bar chart of results">
              <div className="card-title">Visual summary <span>Based on your result</span></div>
              <div className="chart-wrap"><ResponsiveContainer><BarChart data={chartData}><CartesianGrid stroke="#e6ece8" vertical={false} /><XAxis dataKey="x" tickLine={false} axisLine={false} /><YAxis tickLine={false} axisLine={false} /><Tooltip /><Bar dataKey="y" name={cols[yIdx]} fill="#3f9168" radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer></div>
            </div>
          )}
          <div className="table-card">
            <div className="card-title">Result table <span>{cols.length} columns</span></div>
            <div className="table-scroll"><table><thead><tr>{cols.map((c) => <th key={c}>{c}</th>)}</tr></thead><tbody>{rows.map((r, i) => <tr key={i}>{r.map((v, j) => <td key={j}>{v === null ? "—" : String(v)}</td>)}</tr>)}</tbody></table></div>
          </div>
          <div className="code-toggle">
            <button onClick={() => setShowCode(!showCode)} aria-expanded={showCode}><span>{showCode ? "−" : "+"}</span>{showCode ? "Hide" : "Show"} generated Python code</button>
            {showCode && <pre>{result.python_code}</pre>}
          </div>
        </section>
      )}
      <footer>Built for curious minds · Turn spreadsheets into decisions</footer>
    </main>
  );
}
