import React, { useState } from "react";
import { registerParticipant } from "../../api/api";
import "./RegisterForm.css";

const RegisterForm = () => {
  const [hostname, setHostname] = useState("");
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!hostname.trim()) {
      alert("Please enter a hostname");
      return;
    }

    setLoading(true);
    setMessage("");
    setIsError(false);

    try {
      const result = await registerParticipant(hostname);
      setMessage(`✅ Registered successfully!\nTx Hash: ${result.txHash}`);
      setIsError(false);
    } catch (err) {
      console.error("Registration error:", err);
      const reason =
        typeof err === "string"
          ? err
          : err.reason || "Transaction failed or network issue.";
      setMessage(`❌ Registration failed:\n${reason}`);
      setIsError(true);
    } finally {
      setLoading(false);
      setHostname("");
    }
  };

  return (
    <div className="register-container">
      <form onSubmit={handleSubmit} className="register-form">
        <h2 className="form-title">Register Node</h2>

        <div className="form-group">
          <label htmlFor="hostname">Hostname</label>
          <input
            id="hostname"
            type="text"
            value={hostname}
            onChange={(e) => setHostname(e.target.value)}
            placeholder="Enter hostname"
            disabled={loading}
          />
        </div>

        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? "Registering..." : "Register"}
        </button>

        {message && (
          <div
            className={`response-card ${isError ? "error-card" : "success-card"}`}
          >
            <p>{message}</p>
          </div>
        )}
      </form>
    </div>
  );
};

export default RegisterForm;




// import React, { useState } from "react";
// import { registerParticipant } from "../../api/api";
// import "./RegisterForm.css";

// const RegisterForm = () => {
//   const [hostname, setHostname] = useState("");
//   const [loading, setLoading] = useState(false);
//   const [result, setResult] = useState(null);

//   const handleSubmit = async (e) => {
//     e.preventDefault();

//     if (!hostname.trim()) {
//       alert("Please enter a hostname");
//       return;
//     }

//     setLoading(true);
//     setResult(null);

//     try {
//       console.log(`Registering hostname: ${hostname}`);
//       const data = await registerParticipant(hostname);
//       setResult(data);
//     } catch (error) {
//       const errMsg = error.response?.data?.detail || error.message;
//       setResult({ status: "error", message: errMsg });
//     } finally {
//       setLoading(false);
//       setHostname("");
//     }
//   };

//   return (
//     <div className="register-container">
//       <form onSubmit={handleSubmit} className="register-form">
//         <h2 className="form-title">Register Node</h2>

//         <div className="form-group">
//           <label htmlFor="hostname">Hostname</label>
//           <input
//             id="hostname"
//             type="text"
//             value={hostname}
//             onChange={(e) => setHostname(e.target.value)}
//             placeholder="Enter hostname"
//             disabled={loading}
//           />
//         </div>

//         <button type="submit" className="submit-btn" disabled={loading}>
//           {loading ? "Processing..." : "Register"}
//         </button>
//       </form>

//       {/* --- Result Section --- */}
//       {result && (
//         <div className="result-box">
//           {result.status === "success" ? (
//             <>
//               <h3>✅ Registration Successful</h3>
//               <p><strong>Participants:</strong> {result.participants}</p>
//               <p><strong>Result Hash:</strong> {result.result_hash}</p>
//               <p><strong>Tx Hash:</strong> {result.txHash}</p>
//             </>
//           ) : (
//             <>
//               <h3>❌ Registration Failed</h3>
//               <p>{result.message}</p>
//             </>
//           )}
//         </div>
//       )}
//     </div>
//   );
// };

// export default RegisterForm;
