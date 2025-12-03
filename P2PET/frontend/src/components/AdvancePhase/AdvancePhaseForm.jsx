import React, { useState } from "react";
import { advancePhase } from "../../api/api";
import "./AdvancePhaseForm.css";

const AdvancePhaseForm = () => {
  const [hostname, setHostname] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMsg("");

    if (!hostname.trim()) {
      alert("Please enter a hostname");
      return;
    }

    setLoading(true);
    try {
      const res = await advancePhase({ hostname });
      setMsg(res.message || "Phase advanced successfully.");
    } catch (err) {
      console.error("Advance Phase Error:", err);
      setMsg("Failed to advance phase. Please check hostname or backend logs.");
    } finally {
      setLoading(false);
      setHostname("");
    }
  };

  return (
    <div className="advance-container">
      <form onSubmit={handleSubmit} className="advance-form">
        <h2 className="form-title">Advance Phase</h2>

        <div className="form-group">
          <label htmlFor="hostname">Hostname</label>
          <input
            id="hostname"
            type="text"
            value={hostname}
            onChange={(e) => setHostname(e.target.value)}
            placeholder="Enter hostname"
          />
        </div>

        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? "Advancing..." : "Advance Phase"}
        </button>

        {msg && <div className="form-msg">{msg}</div>}
      </form>
    </div>
  );
};

export default AdvancePhaseForm;
