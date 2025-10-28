import React, { useState } from "react";
import { submitExecutionResult } from "../../api/api";
import Button from "../Button/Button";
import "./SubmitExecutionResultForm.css";

const SubmitExecutionResultForm = () => {
  const [hostname, setHostname] = useState("");
  const [loadingSubmit, setLoadingSubmit] = useState(false);
  const [loadingFetch, setLoadingFetch] = useState(false);
  const [msg, setMsg] = useState("");
  const [result, setResult] = useState(null);

  const handleSubmitExecution = async () => {
    if (!hostname.trim()) {
      setMsg("Please enter hostname before submitting.");
      return;
    }

    setLoadingSubmit(true);
    setMsg("");
    setResult(null);
    try {
      const res = await submitExecutionResult({ hostname });
      setResult(res);
      setMsg(res.message || "Execution result submitted successfully.");
    } catch (err) {
      console.error(err);
      setMsg("Failed to submit execution result.");
    } finally {
      setLoadingSubmit(false);
    }
  };

  return (
    <div className="execution-page-center">
      <div className="card-execution-card">
        <div className="form-grid">
          <h2>Submit Execution Hash</h2>

          {/* 🟢 Hostname Field */}
          <div className="form-row">
            <label>Hostname</label>
            <input
              type="text"
              placeholder="Enter hostname"
              value={hostname}
              onChange={(e) => setHostname(e.target.value)}
              className="form-input"
            />
          </div>

          {/* 🟢 Execution Result Field */}
          <div className="form-row">
            <label>Execution Result</label>
            <textarea
              className="execution-textarea"
              value={
                result
                  ? `Status: ${result.status}\nParticipants: ${result.participant_count}\nHash: ${result.result_hash}`
                  : ""
              }
              readOnly
              placeholder="Execution result will appear here..."
            />
          </div>

          {/* 🟢 Buttons */}
          <div className="form-actions">
            <Button
              onClick={handleSubmitExecution}
              text={loadingSubmit ? "Submitting..." : "Submit Execution Result"}
              disabled={loadingSubmit || loadingFetch}
              className="form-btn primary-btn"
            />
          </div>
        </div>

        {msg && <div className="form-msg">{msg}</div>}
      </div>
    </div>
  );
};

export default SubmitExecutionResultForm;
