

import React, { useEffect, useState } from "react";
import {
  getCurrentPhase,
  getCurrentRound,
  getTotalParticipants,
  getNextAvailableSlot,
  getParticipantsList,
  getSubmittedResults,
  getRemainingTimeInPhase,
} from "../../api/api";
import "./StatusPanel.css";

const StatusItem = ({ label, value }) => (
  <div className="stat">
    <div className="stat-label">{label}</div>
    <div className="stat-value">{value}</div>
  </div>
);

const StatusPanel = () => {
  const [phase, setPhase] = useState("-");
  const [round, setRound] = useState("-");
  const [total, setTotal] = useState("-");
  const [nextSlot, setNextSlot] = useState("-");
  const [participants, setParticipants] = useState([]);
  const [submittedResults, setSubmittedResults] = useState([]);
  const [expanded, setExpanded] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [error, setError] = useState("");

  const [remainingTime, setRemainingTime] = useState("-");
  const [liveTime, setLiveTime] = useState(null);

  // 🔁 Fetch data
  const refresh = async () => {
    try {
      setError("");

      const results = await Promise.allSettled([
        getCurrentPhase(),
        getCurrentRound(),
        getTotalParticipants(),
        getNextAvailableSlot(),
        getParticipantsList(),
        getSubmittedResults(),
        getRemainingTimeInPhase(),
      ]);

      const [
        phaseRes,
        roundRes,
        totalRes,
        slotRes,
        participantsRes,
        submittedRes,
        remainingTimeRes,
      ] = results;

      if (phaseRes.status === "fulfilled")
        setPhase(phaseRes.value.currentPhase ?? "-");

      if (roundRes.status === "fulfilled")
        setRound(roundRes.value.currentRound ?? "-");

      if (totalRes.status === "fulfilled")
        setTotal(totalRes.value.TOTAL_PARTICIPANTS ?? "-");

      if (slotRes.status === "fulfilled")
        setNextSlot(slotRes.value.nextAvailableSlot ?? "-");

      if (remainingTimeRes.status === "fulfilled") {
        const time =
          remainingTimeRes.value?.remainingTimeInPhase ?? "-";

        setRemainingTime(time);
        setLiveTime(typeof time === "number" ? time : null);
      }

      if (participantsRes.status === "fulfilled") {
        setParticipants(
          participantsRes.value.participantsList ?? []
        );
      }

      if (submittedRes.status === "fulfilled") {
        setSubmittedResults(
          submittedRes.value.submittedResults ?? []
        );
      }
    } catch (err) {
      console.error("Status refresh failed:", err);
      setError("Failed to load status. Check console for details.");
    }
  };

  // 🔁 API refresh every 8 sec
  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 8000);
    return () => clearInterval(id);
  }, []);

  // ⏱️ Live countdown every 1 sec
  useEffect(() => {
    const timer = setInterval(() => {
      setLiveTime((prev) => {
        if (prev === null || prev <= 0) return prev;
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // ⏱️ Format MM:SS
  const formatTime = (seconds) => {
    if (seconds === null || seconds === "-" || seconds === undefined)
      return "-";

    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;

    return `${mins.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
  };

  return (
    <div className="status-center">
      <div className="card status-card">
        <div className="status-head">
          <h3>Marketplace Round Status</h3>
          <button className="refresh" onClick={refresh}>
            ↻
          </button>
        </div>

        {error && <div className="error-msg">{error}</div>}

        <div className="stats-grid">
          <StatusItem label="Current Phase" value={phase} />
          <StatusItem label="Current Round" value={round} />
          <StatusItem label="Total Participants" value={total} />
          <StatusItem label="Next Free Slot" value={nextSlot} />
          <StatusItem
            label="Remaining Time "
            value={formatTime(liveTime ?? remainingTime)}
          />
        </div>

        {/* Participants */}
        <div className="participants-section">
          <div className="participants-header">
            <h3>Participants List</h3>
            <button
              className="toggle-btn"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? "▲ Hide" : "▼ Show"}
            </button>
          </div>

          {expanded && (
            <>
              {participants.length > 0 ? (
                <table className="participants-table">
                  <thead>
                    <tr>
                      <th>Address</th>
                      <th>Role</th>
                      <th>Energy (kWh)</th>
                      <th>Price (Rs)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {participants.map((p, idx) => (
                      <tr key={idx}>
                        <td>{p[0]}</td>
                        <td>
                          {p[1] === 1
                            ? "Buyer"
                            : p[1] === 2
                            ? "Seller"
                            : "N/A"}
                        </td>
                        <td>{(p[2] / 100).toFixed(0)}</td>
                        <td>{(p[3] / 100).toFixed(0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p>No participants found.</p>
              )}
            </>
          )}
        </div>

        {/* Submitted Results */}
        <div className="submitted-section">
          <div className="participants-header">
            <h3>Submitted Execution Results</h3>
            <button
              className="toggle-btn"
              onClick={() => setShowResults(!showResults)}
            >
              {showResults ? "▲ Hide" : "▼ Show"}
            </button>
          </div>

          {showResults && (
            <>
              {submittedResults.length > 0 ? (
                <table className="participants-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Submitter</th>
                      <th>Result Hash</th>
                    </tr>
                  </thead>
                  <tbody>
                    {submittedResults.map((r, idx) => (
                      <tr key={idx}>
                        <td>{idx + 1}</td>
                        <td>{r.submitter}</td>
                        <td className="hash-cell">{r.resultHash}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p>No submitted results found.</p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default StatusPanel;