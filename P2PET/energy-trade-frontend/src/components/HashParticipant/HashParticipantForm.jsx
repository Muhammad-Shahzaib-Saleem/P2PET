// import React, { useState } from "react";
// import { hashParticipants } from "../../api/api";
// import Button from "../Button/Button";
// import "./HashParticipantForm.css";

// const HashParticipantForm = () => {
//   const [hostname, setHostname] = useState("");
//   const [computedHash, setComputedHash] = useState("");
//   const [loading, setLoading] = useState(false);
//   const [msg, setMsg] = useState("");

//   const handleHash = async () => {
//     if (!hostname.trim()) {
//       alert("Please enter a hostname");
//       return;
//     }

//     setLoading(true);
//     setMsg("");
//     try {
//       const res = await hashParticipants({ hostname });
//       setComputedHash(res.computedHash || "No hash returned.");
//       setMsg(res.message || "Hash computed successfully.");
//     } catch (err) {
//       console.error(err);
//       setMsg("Failed to compute hash. Check console for details.");
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div className="hash-page-center">
//       <div className="hash-container">
//         <h2>Hash Participant</h2>

//         <div className="form-grid">
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
//             <label>Computed Hash</label>
//             <textarea
//               className="hash-textarea"
//               value={computedHash}
//               readOnly
//               placeholder="Hash will appear here after computation..."
//             />
//           </div>

//           <div className="form-actions">
//             <Button
//               onClick={handleHash}
//               text={loading ? "Computing..." : "Compute Hash"}
//               disabled={loading}
//               full
//             />
//           </div>
//         </div>

//         {msg && <div className="form-msg">{msg}</div>}
//       </div>
//     </div>
//   );
// };

// export default HashParticipantForm;


import React, { useState } from "react";
import { hashParticipants } from "../../api/api";
import Button from "../Button/Button";
import "./HashParticipantForm.css";

const HashParticipantForm = () => {
  const [hostname, setHostname] = useState("");
  const [computedHash, setComputedHash] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [revertReason, setRevertReason] = useState("");
  const [txHash, setTxHash] = useState("");
  const [explorerUrl, setExplorerUrl] = useState("");

  const handleHash = async () => {
    if (!hostname.trim()) {
      alert("Please enter a hostname");
      return;
    }

    setLoading(true);
    setMsg("");
    setComputedHash("");
    setRevertReason("");
    setTxHash("");
    setExplorerUrl("");

    try {
      const res = await hashParticipants({ hostname });

      if (res.status === "success") {
        setComputedHash(res.computedHash || "No hash returned.");
        setMsg(res.message || "Hash computed successfully.");
        setTxHash(res.txHash || "");
        setExplorerUrl(res.explorerUrl || "");
        setRevertReason(res.revert_reason || "");
      } else {
        setMsg("❌ Transaction failed.");
        setRevertReason(res.revert_reason || "Unknown error");
      }
    } catch (err) {
      console.error("Error computing hash:", err);

      if (err.response && err.response.data && err.response.data.detail) {
        const detail = err.response.data.detail;
        setRevertReason(
          typeof detail === "object" ? JSON.stringify(detail, null, 2) : detail
        );
        setMsg("❌ Transaction failed.");
      } else {
        setMsg("❌ Failed to compute hash. Check console for details.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="hash-page-center">
      <div className="hash-container">
        <h2>Hash Participants</h2>

        <div className="form-grid">
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

          {/* Computed Hash — always visible */}
          <div className="form-row">
            <label>Computed Hash</label>
            <textarea
              className="hash-textarea"
              value={computedHash}
              readOnly
              placeholder="Hash will appear here after computation..."
            />
          </div>

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
              onClick={handleHash}
              text={loading ? "Computing..." : "Compute Hash"}
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

export default HashParticipantForm;

