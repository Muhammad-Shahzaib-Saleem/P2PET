import React, { useState } from "react";
import { verifyExecution } from "../../api/api";
import Button from "../Button/Button";
import "./VerifyExecutionResultForm.css";

const VerifyExecutionResultForm = () => {
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [result, setResult] = useState(null);

  const handleVerify = async () => {
    setLoading(true);
    setMsg("");
    setResult(null);
    try {
      const res = await verifyExecution();
      setResult(res);
      setMsg(res.message || "Verification successful.");
    } catch (err) {
      console.error(err);
      setMsg("Verification failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="execution-page-center">
      <div className="card execution-card">
        <div className="form-grid">
          <div className="form-row">
            <h2>Verify Execution Hash</h2>
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
