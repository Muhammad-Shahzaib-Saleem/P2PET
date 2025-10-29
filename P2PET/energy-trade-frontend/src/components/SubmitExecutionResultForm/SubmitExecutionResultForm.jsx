// import React, { useState } from "react";
// import { submitExecutionResult } from "../../api/api";
// import Button from "../Button/Button";
// import "./SubmitExecutionResultForm.css";

// const SubmitExecutionResultForm = () => {
//   const [hostname, setHostname] = useState("");
//   const [loadingSubmit, setLoadingSubmit] = useState(false);
//   const [loadingFetch, setLoadingFetch] = useState(false);
//   const [msg, setMsg] = useState("");
//   const [result, setResult] = useState(null);

//   const handleSubmitExecution = async () => {
//     if (!hostname.trim()) {
//       setMsg("Please enter hostname before submitting.");
//       return;
//     }

//     setLoadingSubmit(true);
//     setMsg("");
//     setResult(null);
//     try {
//       const res = await submitExecutionResult({ hostname });
//       setResult(res);
//       setMsg(res.message || "Execution result submitted successfully.");
//     } catch (err) {
//       console.error(err);
//       setMsg("Failed to submit execution result.");
//     } finally {
//       setLoadingSubmit(false);
//     }
//   };

//   return (
//     <div className="execution-page-center">
//       <div className="card-execution-card">
//         <div className="form-grid">
//           <h2>Submit Execution Hash</h2>

//           {/* 🟢 Hostname Field */}
//           <div className="form-row">
//             <label>Hostname</label>
//             <input
//               type="text"
//               placeholder="Enter hostname"
//               value={hostname}
//               onChange={(e) => setHostname(e.target.value)}
//               className="form-input"
//             />
//           </div>

//           {/* 🟢 Execution Result Field */}
//           <div className="form-row">
//             <label>Execution Result</label>
//             <textarea
//               className="execution-textarea"
//               value={
//                 result
//                   ? `Status: ${result.status}\nParticipants: ${result.participant_count}\nHash: ${result.result_hash}`
//                   : ""
//               }
//               readOnly
//               placeholder="Execution result will appear here..."
//             />
//           </div>

//           {/* 🟢 Buttons */}
//           <div className="form-actions">
//             <Button
//               onClick={handleSubmitExecution}
//               text={loadingSubmit ? "Submitting..." : "Submit Execution Result"}
//               disabled={loadingSubmit || loadingFetch}
//               className="form-btn primary-btn"
//             />
//           </div>
//         </div>

//         {msg && <div className="form-msg">{msg}</div>}
//       </div>
//     </div>
//   );
// };

// export default SubmitExecutionResultForm;

import React, { useState } from "react";
import { submitExecutionResult } from "../../api/api";
import Button from "../Button/Button";
import "./SubmitExecutionResultForm.css";

const SubmitExecutionResultForm = () => {
  const [hostname, setHostname] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [result, setResult] = useState(null);
  const [revertReason, setRevertReason] = useState("");
  const [txHash, setTxHash] = useState("");
  const [explorerUrl, setExplorerUrl] = useState("");

  const handleSubmitExecution = async () => {
    if (!hostname.trim()) {
      setMsg("Please enter hostname before submitting.");
      return;
    }

    setLoading(true);
    setMsg("");
    setResult(null);
    setRevertReason("");
    setTxHash("");
    setExplorerUrl("");

    try {
      const res = await submitExecutionResult({ hostname });

      if (res.status === "success") {
        setResult(res);
        setMsg(res.message || "Execution result submitted successfully.");
        setTxHash(res.txHash || "");
        setExplorerUrl(res.explorerUrl || "");
        setRevertReason(res.revert_reason || "");
      } else {
        setResult(res);
        setMsg("❌ Transaction failed.");
        setRevertReason(res.revert_reason || "Unknown error");
      }
    } catch (err) {
      console.error(err);
      if (err.response && err.response.data && err.response.data.detail) {
        const detail = err.response.data.detail;
        setRevertReason(
          typeof detail === "object" ? JSON.stringify(detail, null, 2) : detail
        );
        setMsg("❌ Transaction failed.");
      } else {
        setMsg("❌ Failed to submit execution result. Check console for details.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="execution-page-center">
      <div className="card-execution-card">
        <h2>Submit Execution Hash</h2>

        <div className="form-grid">
          {/* Hostname Input */}
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

          {/* Execution Result Textarea */}
          <div className="form-row">
            <label>Execution Result</label>
            <textarea
              className="execution-textarea"
              value={
                result
                  ? `Status: ${result.status}\nParticipants: ${result.participant_count || 0}\nHash: ${result.result_hash || ""}`
                  : ""
              }
              readOnly
              placeholder="Execution result will appear here..."
            />
          </div>

          {/* Transaction Hash + Explorer */}
          {txHash && (
            <div className="form-row">
              <label>Transaction Hash</label>
              <div className="tx-box">
                <span className="tx-hash">{txHash}</span>
                {explorerUrl && (
                  <a
                    href={explorerUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="explorer-link"
                  >
                    View on Explorer 🔗
                  </a>
                )}
              </div>
            </div>
          )}

          {/* Revert Reason */}
          {revertReason && (
            <div className="form-row revert-reason">
              <label>Revert Reason</label>
              <div className="revert-box">
                {typeof revertReason === "object"
                  ? JSON.stringify(revertReason, null, 2)
                  : revertReason}
              </div>
            </div>
          )}

          {/* Submit Button */}
          <div className="form-actions">
            <Button
              onClick={handleSubmitExecution}
              text={loading ? "Submitting..." : "Submit Execution Result"}
              disabled={loading}
              full
            />
          </div>
        </div>

        {msg && <div className="form-msg">{msg}</div>}
      </div>
    </div>
  );
};

export default SubmitExecutionResultForm;
