import React, { useState } from "react";
import { hashParticipants } from "../../api/api";
import Button from "../Button/Button";
import "./HashParticipantForm.css";

const HashParticipantForm = () => {
  const [hostname, setHostname] = useState("");
  const [computedHash, setComputedHash] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const handleHash = async () => {
    if (!hostname.trim()) {
      alert("Please enter a hostname");
      return;
    }

    setLoading(true);
    setMsg("");
    try {
      const res = await hashParticipants({ hostname });
      setComputedHash(res.computedHash || "No hash returned.");
      setMsg(res.message || "Hash computed successfully.");
    } catch (err) {
      console.error(err);
      setMsg("Failed to compute hash. Check console for details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="hash-page-center">
      <div className="hash-container">
        <h2>Hash Participant</h2>

        <div className="form-grid">
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
            <label>Computed Hash</label>
            <textarea
              className="hash-textarea"
              value={computedHash}
              readOnly
              placeholder="Hash will appear here after computation..."
            />
          </div>

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
