// import React, { useState } from "react";
// import { verifyExecution } from "../../api/api";
// import Button from "../Button/Button";
// import "./VerifyExecutionResultForm.css";

// const VerifyExecutionResultForm = () => {
//   const [hostname, setHostname] = useState("");
//   const [loading, setLoading] = useState(false);
//   const [msg, setMsg] = useState("");
//   const [result, setResult] = useState(null);

//   const handleVerify = async () => {
//     if (!hostname.trim()) {
//       alert("Please enter a hostname");
//       return;
//     }

//     setLoading(true);
//     setMsg("");
//     setResult(null);
//     try {
//       const res = await verifyExecution({ hostname });
//       setResult(res);
//       setMsg(res.message || "Verification successful.");
//     } catch (err) {
//       console.error(err);
//       setMsg("Verification failed. Check console for details.");
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div className="execution-page-center">
//       <div className="card-execution-card">
//         <div className="form-grid">
//           <h2>Verify Execution Hash</h2>

//           <div className="form-row">
//             <label htmlFor="hostname">Hostname</label>
//             <input
//               id="hostname"
//               type="text"
//               value={hostname}
//               onChange={(e) => setHostname(e.target.value)}
//               placeholder="Enter hostname"
//             />
//           </div>

//           <div className="form-row">
//             <label>Verification Result</label>
//             <textarea
//               className="execution-textarea"
//               value={
//                 result
//                   ? `Majority Hash: ${result.majority_hash}\nVerified: ${result.is_verified}`
//                   : ""
//               }
//               readOnly
//               placeholder="Verification result will appear here..."
//             />
//           </div>

//           <div className="form-actions">
//             <Button
//               onClick={handleVerify}
//               text={loading ? "Verifying..." : "Verify Execution Result"}
//               disabled={loading}
//               className="form-btn"
//             />
//           </div>
//         </div>

//         {msg && <div className="form-msg">{msg}</div>}
//       </div>
//     </div>
//   );
// };

// export default VerifyExecutionResultForm;

import React, { useState } from "react";
import { verifyExecution } from "../../api/api";
import Button from "../Button/Button";
import "./VerifyExecutionResultForm.css";

const VerifyExecutionResultForm = () => {
  const [hostname, setHostname] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [majorityHash, setMajorityHash] = useState("");
  const [isVerified, setIsVerified] = useState("");
  const [txHash, setTxHash] = useState("");
  const [explorerUrl, setExplorerUrl] = useState("");
  const [revertReason, setRevertReason] = useState("");

  const handleVerify = async () => {
    if (!hostname.trim()) {
      alert("Please enter a hostname");
      return;
    }

    setLoading(true);
    setMsg("");
    setMajorityHash("");
    setIsVerified("");
    setTxHash("");
    setExplorerUrl("");
    setRevertReason("");

    try {
      const res = await verifyExecution({ hostname });

      if (res.status === "success") {
        setMajorityHash(res.majority_hash || "No hash returned.");
        setIsVerified(res.is_verified !== undefined ? res.is_verified.toString() : "false");
        setTxHash(res.txHash || "");
        setExplorerUrl(res.explorerUrl || "");
        setRevertReason(res.revert_reason || "");
        setMsg(res.message || "Verification successful.");
      } else {
        setMsg("Transaction failed.");
        setRevertReason(res.revert_reason || "Unknown error");
      }
    } catch (err) {
      console.error(err);
      if (err.response && err.response.data && err.response.data.detail) {
        const detail = err.response.data.detail;
        setRevertReason(
          typeof detail === "object" ? JSON.stringify(detail, null, 2) : detail
        );
        setMsg("❌ Verification failed.");
      } else {
        setMsg("❌ Verification failed. Check console for details.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="execution-page-center">
      <div className="card-execution-card">
        <div className="form-grid">
          <h2>Verify Execution Hash</h2>

          {/* Hostname Input */}
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

          {/* Computed Hash & Verification */}
          {(majorityHash || isVerified) && (
            <div className="form-row">
              <label>Verification Result</label>
              <textarea
                className="execution-textarea"
                readOnly
                value={`Majority Hash: ${majorityHash}\nVerified: ${isVerified}`}
                placeholder="Verification result will appear here..."
              />
            </div>
          )}

          {/* Transaction Hash + Explorer Link */}
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

          {/* Button */}
          <div className="form-actions">
            <Button
              onClick={handleVerify}
              text={loading ? "Verifying..." : "Verify Execution Result"}
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

export default VerifyExecutionResultForm;
