import React, { useState } from "react";
import { submitTrade } from "../../api/api";
import Button from "../Button/Button";
import "./TradeForm.css";

const clampNonNegative = (v) => (v < 0 ? 0 : v);

const TradeForm = () => {
  const [hostname, setHostname] = useState("");
  const [role, setRole] = useState("buyer");
  const [energy, setEnergy] = useState("");
  const [price, setPrice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [response, setResponse] = useState(null);

  const to2 = (n) => (Number.isFinite(n) ? Number(n.toFixed(2)) : 0);

  const stepNumber = (setter, current, delta) => {
    const n = parseFloat(current || "0");
    const next = clampNonNegative(n + delta);
    setter(String(to2(next)));
  };

  const onNumChange = (setter) => (e) => {
    const v = e.target.value;
    if (v === "") return setter("");
    const n = parseFloat(v);
    if (Number.isNaN(n)) return;
    setter(String(clampNonNegative(n)));
  };

  const onBlur2 = (setter, value) => {
    if (value === "") return;
    const n = parseFloat(value);
    if (Number.isNaN(n)) return;
    setter(String(to2(clampNonNegative(n))));
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setResponse(null);

    if (!hostname.trim())
      return setResponse({ status: "error", message: "❌ Please enter a hostname." });
    if (!energy || Number(energy) <= 0)
      return setResponse({ status: "error", message: "❌ Enter a valid energy amount." });
    if (!price || Number(price) <= 0)
      return setResponse({ status: "error", message: "❌ Enter a valid price." });

    const normEnergy = to2(parseFloat(energy || "0"));
    const normPrice = to2(parseFloat(price || "0"));

    try {
      setSubmitting(true);
      const res = await submitTrade({
        hostname,
        role,
        energy: normEnergy,
        price: normPrice,
      });

      setResponse({
        status: "success",
        message: res.message || "✅ Trade submitted successfully.",
        txHash: res.txHash,
      });

      setHostname("");
      setEnergy("");
      setPrice("");
    } catch (err) {
      console.error("Trade submission error:", err);
      let errorMsg = "❌ Failed to submit trade.";
      let revertReason = "";

      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (typeof detail === "string") errorMsg = `❌ ${detail}`;
        else if (detail.reason)
          revertReason = detail.reason.startsWith("execution reverted:")
            ? detail.reason.replace("execution reverted:", "").trim()
            : detail.reason;
      }

      setResponse({
        status: "error",
        message: errorMsg,
        reason: revertReason,
      });
    } finally {
      setSubmitting(false);
    }
  };

  const explorerBase = "http://localhost:25000/explorer/explorer";

  return (
    <div className="trade-page-center">
      <div className="card trade-card">
        <div className="card-head">
          <h2>Submit Trade</h2>
          <span className="help">
            Provide your hostname, role, energy, and price.
          </span>
        </div>

        <form onSubmit={onSubmit} className="form-grid">
          {/* Hostname */}
          <div className="form-row hostname-input">
            <label>Hostname</label>
            <input
              type="text"
              value={hostname}
              onChange={(e) => setHostname(e.target.value)}
              placeholder="e.g. pi_1"
              disabled={submitting}
              required
            />
          </div>

          {/* Role */}
          <div className="form-row">
            <label>Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              disabled={submitting}
            >
              <option value="buyer">Buyer</option>
              <option value="seller">Seller</option>
            </select>
          </div>

          {/* Energy */}
          <div className="form-row">
            <label>Energy Unit (kWh)</label>
            <div className="number-field">
              <button
                type="button"
                className="stepper-btn"
                onClick={() => stepNumber(setEnergy, energy, -1)}
                disabled={submitting}
              >
                –
              </button>
              <input
                type="number"
                min="0"
                step="0.01"
                value={energy}
                onChange={onNumChange(setEnergy)}
                onBlur={() => onBlur2(setEnergy, energy)}
                placeholder="10.53"
                className="number-input"
                disabled={submitting}
              />
              <button
                type="button"
                className="stepper-btn"
                onClick={() => stepNumber(setEnergy, energy, +1)}
                disabled={submitting}
              >
                +
              </button>
            </div>
          </div>

          {/* Price */}
          <div className="form-row">
            <label>Price</label>
            <div className="number-field">
              <button
                type="button"
                className="stepper-btn"
                onClick={() => stepNumber(setPrice, price, -1)}
                disabled={submitting}
              >
                –
              </button>
              <input
                type="number"
                min="0"
                step="0.01"
                value={price}
                onChange={onNumChange(setPrice)}
                onBlur={() => onBlur2(setPrice, price)}
                placeholder="15.34"
                className="number-input"
                disabled={submitting}
              />
              <button
                type="button"
                className="stepper-btn"
                onClick={() => stepNumber(setPrice, price, +1)}
                disabled={submitting}
              >
                +
              </button>
            </div>
          </div>

          <div className="form-actions">
            <Button
              type="submit"
              text={submitting ? "Submitting..." : "Submit Trade"}
              loading={submitting}
              full
            />
          </div>
        </form>

        {/* ✅ Response message */}
        {response && (
          <div
            className={`response-box ${
              response.status === "error" ? "error" : "success"
            }`}
          >
            <p className="response-text">{response.message}</p>

            {response.txHash && (
              <div className="tx-section">
                <p className="tx-hash">
                  <strong>Tx Hash:</strong> {response.txHash}
                </p>
                <a
                  href={`${explorerBase}?hash=${response.txHash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="explorer-link"
                >
                  🔗 View on Explorer
                </a>
              </div>
            )}

            {response.reason && (
              <p className="revert-reason">
                ❌ <strong>Revert reason:</strong> {response.reason}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TradeForm;




// import React, { useState } from "react";
// import { submitTrade } from "../../api/api";
// import Button from "../Button/Button";
// import "./TradeForm.css";

// const clampNonNegative = (v) => (v < 0 ? 0 : v);

// const TradeForm = () => {
//   const [hostname, setHostname] = useState("");
//   const [role, setRole] = useState("buyer");
//   const [energy, setEnergy] = useState("");
//   const [price, setPrice] = useState("");
//   const [submitting, setSubmitting] = useState(false);
//   const [message, setMessage] = useState("");
//   const [isError, setIsError] = useState(false);

//   const to2 = (n) => (Number.isFinite(n) ? Number(n.toFixed(2)) : 0);

//   const stepNumber = (setter, current, delta) => {
//     const n = parseFloat(current || "0");
//     const next = clampNonNegative(n + delta);
//     setter(String(to2(next)));
//   };

//   const onNumChange = (setter) => (e) => {
//     const v = e.target.value;
//     if (v === "") return setter("");
//     const n = parseFloat(v);
//     if (Number.isNaN(n)) return;
//     setter(String(clampNonNegative(n)));
//   };

//   const onBlur2 = (setter, value) => {
//     if (value === "") return;
//     const n = parseFloat(value);
//     if (Number.isNaN(n)) return;
//     setter(String(to2(clampNonNegative(n))));
//   };

//   const onSubmit = async (e) => {
//     e.preventDefault();
//     setMessage("");
//     setIsError(false);

//     if (!hostname.trim()) {
//       setMessage("❌ Please enter a hostname.");
//       setIsError(true);
//       return;
//     }
//     if (!energy || Number(energy) <= 0) {
//       setMessage("❌ Enter a valid energy amount.");
//       setIsError(true);
//       return;
//     }
//     if (!price || Number(price) <= 0) {
//       setMessage("❌ Enter a valid price.");
//       setIsError(true);
//       return;
//     }

//     const normEnergy = to2(parseFloat(energy || "0"));
//     const normPrice = to2(parseFloat(price || "0"));

//     try {
//       setSubmitting(true);
//       const res = await submitTrade({
//         hostname,
//         role,
//         energy: normEnergy,
//         price: normPrice,
//       });

//       setMessage(
//         `✅ ${res.message || "Trade submitted successfully."} ${
//           res.txHash ? `Tx Hash: ${res.txHash}` : ""
//         }`
//       );
//       setIsError(false);
//       setHostname("");
//       setEnergy("");
//       setPrice("");
//     } catch (err) {
//       console.error("Trade submission error:", err);
//       let errorMsg = "❌ Failed to submit trade.";

//       if (err.response?.data?.detail) {
//         const detail = err.response.data.detail;
//         if (typeof detail === "string") {
//           errorMsg = `❌ ${detail}`;
//         } else if (detail.reason) {
//           errorMsg = `❌ Transaction failed: ${detail.reason}`;
//         } else if (detail.message) {
//           errorMsg = `❌ ${detail.message}`;
//         }
//       }

//       setMessage(errorMsg);
//       setIsError(true);
//     } finally {
//       setSubmitting(false);
//     }
//   };

//   return (
//     <div className="trade-page-center">
//       <div className="card trade-card">
//         <div className="card-head">
//           <h2>Submit Trade</h2>
//           <span className="help">
//             Provide your hostname, role, energy, and price.
//           </span>
//         </div>

//         <form onSubmit={onSubmit} className="form-grid">
//           {/* Hostname */}
//           <div className="form-row hostname-input">
//             <label>Hostname</label>
//             <input
//               type="text"
//               value={hostname}
//               onChange={(e) => setHostname(e.target.value)}
//               placeholder="e.g. pi_1"
//               disabled={submitting}
//               required
//             />
//           </div>

//           {/* Role */}
//           <div className="form-row">
//             <label>Role</label>
//             <select
//               value={role}
//               onChange={(e) => setRole(e.target.value)}
//               disabled={submitting}
//             >
//               <option value="buyer">Buyer</option>
//               <option value="seller">Seller</option>
//             </select>
//           </div>

//           {/* Energy */}
//           <div className="form-row">
//             <label>Energy Unit (kWh)</label>
//             <div className="number-field">
//               <button
//                 type="button"
//                 className="stepper-btn"
//                 onClick={() => stepNumber(setEnergy, energy, -1)}
//                 disabled={submitting}
//               >
//                 –
//               </button>
//               <input
//                 type="number"
//                 min="0"
//                 step="0.01"
//                 value={energy}
//                 onChange={onNumChange(setEnergy)}
//                 onBlur={() => onBlur2(setEnergy, energy)}
//                 placeholder="10.53"
//                 className="number-input"
//                 disabled={submitting}
//               />
//               <button
//                 type="button"
//                 className="stepper-btn"
//                 onClick={() => stepNumber(setEnergy, energy, +1)}
//                 disabled={submitting}
//               >
//                 +
//               </button>
//             </div>
//           </div>

//           {/* Price */}
//           <div className="form-row">
//             <label>Price</label>
//             <div className="number-field">
//               <button
//                 type="button"
//                 className="stepper-btn"
//                 onClick={() => stepNumber(setPrice, price, -1)}
//                 disabled={submitting}
//               >
//                 –
//               </button>
//               <input
//                 type="number"
//                 min="0"
//                 step="0.01"
//                 value={price}
//                 onChange={onNumChange(setPrice)}
//                 onBlur={() => onBlur2(setPrice, price)}
//                 placeholder="15.34"
//                 className="number-input"
//                 disabled={submitting}
//               />
//               <button
//                 type="button"
//                 className="stepper-btn"
//                 onClick={() => stepNumber(setPrice, price, +1)}
//                 disabled={submitting}
//               >
//                 +
//               </button>
//             </div>
//           </div>

//           <div className="form-actions">
//             <Button
//               type="submit"
//               text={submitting ? "Submitting..." : "Submit Trade"}
//               loading={submitting}
//               full
//             />
//           </div>
//         </form>

//         {/* ✅ Response message inside card */}
//         {message && (
//           <div className={`response-message ${isError ? "error" : "success"}`}>
//             {message}
//           </div>
//         )}
//       </div>
//     </div>
//   );
// };

// export default TradeForm;

