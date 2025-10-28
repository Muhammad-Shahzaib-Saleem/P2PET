import React, { useState } from "react";
import { verifyExecution } from "../../api/api";
import Button from "../Button/Button";
import "./VerifyExecutionResultForm.css";

const VerifyExecutionResultForm = () => {
  const [hostname, setHostname] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [result, setResult] = useState(null);

  const handleVerify = async () => {
    if (!hostname.trim()) {
      alert("Please enter a hostname");
      return;
    }

    setLoading(true);
    setMsg("");
    setResult(null);
    try {
      const res = await verifyExecution({ hostname });
      setResult(res);
      setMsg(res.message || "Verification successful.");
    } catch (err) {
      console.error(err);
      setMsg("Verification failed. Check console for details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="execution-page-center">
      <div className="card-execution-card">
        <div className="form-grid">
          <h2>Verify Execution Hash</h2>

          <div className="form-row">
            <label htmlFor="hostname">Hostname</label>
            <input
              id="hostname"
              type="text"
              value={hostname}
              onChange={(e) => setHostname(e.target.value)}
              placeholder="Enter hostname"
            />
          </div>

          <div className="form-row">
            <label>Verification Result</label>
            <textarea
              className="execution-textarea"
              value={
                result
                  ? `Majority Hash: ${result.majority_hash}\nVerified: ${result.is_verified}`
                  : ""
              }
              readOnly
              placeholder="Verification result will appear here..."
            />
          </div>

          <div className="form-actions">
            <Button
              onClick={handleVerify}
              text={loading ? "Verifying..." : "Verify Execution Result"}
              disabled={loading}
              className="form-btn"
            />
          </div>
        </div>

        {msg && <div className="form-msg">{msg}</div>}
      </div>
    </div>
  );
};

export default VerifyExecutionResultForm;
