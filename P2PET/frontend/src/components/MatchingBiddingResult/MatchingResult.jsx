import React, { useEffect, useState } from "react";
import { getBiddingResults } from "../../api/api";
import "./MatchingResult.css";

const StatusItem = ({ label, value }) => (
  <div className="stat">
    <div className="stat-label">{label}</div>
    <div className="stat-value">{value}</div>
  </div>
);

const MatchingResult = () => {
  const [results, setResults] = useState([]);
  const [expanded, setExpanded] = useState(false);
  const [error, setError] = useState("");

  // 🔁 Fetch data
  const refresh = async () => {
  try {
    setError("");

    const res = await getBiddingResults();

    if (!res || res.status !== "success") {
      setResults([]);  // clear UI
      setError("No valid bidding data.");
      return;
    }

    setResults(res.data ?? []);
  } catch (err) {
    console.error("Bidding results fetch failed:", err);
    setError("Failed to load bidding results.");
    setResults([]);  // clear UI
  }
};

  // 🔁 Auto refresh every 8 sec
  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 8000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="status-center">
      <div className="card status-card">
        <div className="status-head">
          <h3>⚡ Bidding Results</h3>
          <button className="refresh" onClick={refresh}>
            ↻
          </button>
        </div>

        {error && <div className="error-msg">{error}</div>}

        {/* Summary */}
        <div className="stats-grid">
          <StatusItem label="Total Matches" value={results.length} />
        </div>

        {/* Results Section */}
        <div className="participants-section">
          <div className="participants-header">
            <h3>Matched Trades</h3>
            <button
              className="toggle-btn"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? "▲ Hide" : "▼ Show"}
            </button>
          </div>

          {expanded && (
            <>
              {results.length > 0 ? (
                <table className="participants-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Buyer</th>
                      <th>Seller</th>
                      <th>Energy (kWh)</th>
                      <th>Price</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((r, idx) => (
                      <tr key={idx}>
                        <td>{idx + 1}</td>
                        <td className="hash-cell" title={r.buyer_id}>{r.buyer_id} </td>
                        <td className="hash-cell" title={r.seller_id}>{r.seller_id}</td>
                        <td>{r.energy_matched}</td>
                        <td>{r.price}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p>No bidding results found.</p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default MatchingResult;