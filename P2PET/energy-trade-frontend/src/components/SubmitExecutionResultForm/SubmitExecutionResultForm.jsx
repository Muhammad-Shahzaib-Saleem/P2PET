import React, { useState } from "react";
import { submitExecutionResult, /*getExecutionResult*/ } from "../../api/api";
import Button from "../Button/Button";
import "./SubmitExecutionResultForm.css";

const SubmitExecutionResultForm = () => {
  const [loadingSubmit, setLoadingSubmit] = useState(false);
  const [loadingFetch, setLoadingFetch] = useState(false);
  const [msg, setMsg] = useState("");
  const [result, setResult] = useState(null);

  const handleSubmitExecution = async () => {
    setLoadingSubmit(true);
    setMsg("");
    setResult(null);
    try {
      const res = await submitExecutionResult();
      setResult(res);
      setMsg(res.message || "Execution result submitted successfully.");
    } catch (err) {
      console.error(err);
      setMsg("Failed to submit execution result.");
    } finally {
      setLoadingSubmit(false);
    }
  };

  const handleViewExecution = async () => {
    setLoadingFetch(true);
    setMsg("");
    try {
      const res = await getExecutionResult();
      setResult(res);
      setMsg("Execution result fetched successfully.");
    } catch (err) {
      console.error(err);
      setMsg("Failed to fetch execution result.");
    } finally {
      setLoadingFetch(false);
    }
  };

  return (
    <div className="execution-page-center">
      <div className="card execution-card">
        <div className="form-grid">
          <div className="form-row">
            <h2>Submit Execution Hash</h2>
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

          <div className="form-actions">
            <Button
              onClick={handleSubmitExecution}
              text={loadingSubmit ? "Submitting..." : "Submit Execution Result"}
              disabled={loadingSubmit || loadingFetch}
              className="form-btn primary-btn"
            />
            <Button
              onClick={handleViewExecution}
              text={loadingFetch ? "Fetching..." : "View Execution Result"}
              disabled={loadingSubmit || loadingFetch}
              className="form-btn secondary-btn"
            />
          </div>
        </div>

        {msg && <div className="form-msg">{msg}</div>}
      </div>
    </div>
  );
};

export default SubmitExecutionResultForm;
