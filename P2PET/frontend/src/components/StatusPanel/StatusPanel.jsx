// import React, { useEffect, useState } from "react";
// import {
//   getCurrentPhase,
//   getCurrentRound,
//   getTotalParticipants,
//   getNextAvailableSlot,
//   getParticipantsList,
//   getSubmittedResults,
//   getRemainingTimeInPhase,
//   getEnergyTransferingTime,
// } from "../../api/api";
// import "./StatusPanel.css";

// const StatusItem = ({ label, value }) => (
//   <div className="stat">
//     <div className="stat-label">{label}</div>
//     <div className="stat-value">{value}</div>
//   </div>
// );

// const StatusPanel = () => {
//   const [phase, setPhase]                       = useState("-");
//   const [round, setRound]                       = useState("-");
//   const [total, setTotal]                       = useState("-");
//   const [nextSlot, setNextSlot]                 = useState("-");
//   const [participants, setParticipants]         = useState([]);
//   const [submittedResults, setSubmittedResults] = useState([]);
//   const [expanded, setExpanded]                 = useState(false);
//   const [showResults, setShowResults]           = useState(false);
//   const [error, setError]                       = useState("");

//   const [remainingTime, setRemainingTime]       = useState("-");
//   const [liveTime, setLiveTime]                 = useState(null);

//   // ── Transfer window state ──────────────────────────────────────────────
//   const [transferWindow, setTransferWindow]         = useState(null);   // ← was missing
//   const [liveTransferTime, setLiveTransferTime]     = useState(null);   // ← was missing

//   // ─── Fetch all data ────────────────────────────────────────────────────
//   const refresh = async () => {
//     try {
//       setError("");

//       const results = await Promise.allSettled([
//         getCurrentPhase(),
//         getCurrentRound(),
//         getTotalParticipants(),
//         getNextAvailableSlot(),
//         getParticipantsList(),
//         getSubmittedResults(),
//         getRemainingTimeInPhase(),
//         getEnergyTransferingTime(),
//       ]);

//       const [
//         phaseRes,
//         roundRes,
//         totalRes,
//         slotRes,
//         participantsRes,
//         submittedRes,
//         remainingTimeRes,
//         energyTransferTimeRes,   // ← correct name, was called transferWindowRes below
//       ] = results;

//       if (phaseRes.status === "fulfilled")
//         setPhase(phaseRes.value.currentPhase ?? "-");

//       if (roundRes.status === "fulfilled")
//         setRound(roundRes.value.currentRound ?? "-");

//       if (totalRes.status === "fulfilled")
//         setTotal(totalRes.value.TOTAL_PARTICIPANTS ?? "-");

//       if (slotRes.status === "fulfilled")
//         setNextSlot(slotRes.value.nextAvailableSlot ?? "-");

//       // if (remainingTimeRes.status === "fulfilled") {
//       //   const time = remainingTimeRes.value?.remainingTimeInPhase ?? "-";
//       //   setRemainingTime(time);
//       //   setLiveTime(typeof time === "number" ? time : null);
//       // }

//       if (remainingTimeRes.status === "fulfilled") {
//   const time = remainingTimeRes.value?.remainingTimeInPhase ?? "-";
//   setRemainingTime(time);

//   setLiveTime((prev) => {
//     if (typeof time !== "number") return null;
//     if (prev === null) return time;        // first load
//     if (time > prev) return prev;          // ← NEVER go up, ignore higher server value
//     if (Math.abs(prev - time) > 5) return time;  // resync only if drifted too low
//     return prev;                           // keep local countdown
//   });
// }

//       if (participantsRes.status === "fulfilled")
//         setParticipants(participantsRes.value.participantsList ?? []);

//       if (submittedRes.status === "fulfilled")
//         setSubmittedResults(submittedRes.value.submittedResults ?? []);

//       // ── Transfer window ── was using wrong variable name "transferWindowRes"
//       // if (energyTransferTimeRes.status === "fulfilled") {
//       //   const tw = energyTransferTimeRes.value;
//       //   setTransferWindow(tw);
//       //   setLiveTransferTime(
//       //     tw?.isOpen && typeof tw?.remainingSeconds === "number"
//       //       ? tw.remainingSeconds
//       //       : null
//       //   );
//       // }

//       setLiveTransferTime((prev) => {
//   if (!tw?.isOpen || typeof tw?.remainingSeconds !== "number") return null;
//   if (prev === null) return tw.remainingSeconds;
//   if (tw.remainingSeconds > prev) return prev;          // ← NEVER go up
//   if (Math.abs(prev - tw.remainingSeconds) > 5) return tw.remainingSeconds;
//   return prev;
// });

//     } catch (err) {
//       console.error("Status refresh failed:", err);
//       setError("Failed to load status. Check console for details.");
//     }
//   };

//   // 🔁 API refresh every 8 sec
//   useEffect(() => {
//     refresh();
//     const id = setInterval(refresh, 8000);
//     return () => clearInterval(id);
//   }, []);

//   // ⏱️ Phase countdown every 1 sec
//   useEffect(() => {
//     const timer = setInterval(() => {
//       setLiveTime((prev) => {
//         if (prev === null || prev <= 0) return prev;
//         return prev - 1;
//       });
//     }, 1000);
//     return () => clearInterval(timer);   // ← was missing closing brace + return
//   }, []);

//   // ⏱️ Transfer window countdown every 1 sec  ← was nested inside phase useEffect
//   useEffect(() => {
//     const timer = setInterval(() => {
//       setLiveTransferTime((prev) => {
//         if (prev === null || prev <= 0) return prev;
//         return prev - 1;
//       });
//     }, 1000);
//     return () => clearInterval(timer);
//   }, []);

//   // ⏱️ Format MM:SS
//   const formatTime = (seconds) => {
//     if (seconds === null || seconds === "-" || seconds === undefined)
//       return "-";
//     const mins = Math.floor(seconds / 60);
//     const secs = seconds % 60;
//     return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
//   };

//   // ── Transfer window badge ──────────────────────────────────────────────
//   const transferBadge = () => {
//     if (!transferWindow) return { label: "-", className: "badge-idle" };

//     switch (transferWindow.status) {
//       case "not_started":
//         return { label: "Not Started", className: "badge-idle" };
//       case "open":
//         return {
//           label: transferWindow.transferRound < transferWindow.currentRound
//             ? `Round ${transferWindow.transferRound} Overlap`
//             : "Open",
//           className: "badge-open",
//         };
//       case "closed":
//         return { label: "Closed", className: "badge-closed" };
//       default:
//         return { label: "-", className: "badge-idle" };
//     }
//   };

//   const { label: badgeLabel, className: badgeClass } = transferBadge(); // ← was missing

//   return (
//     <div className="status-center">
//       <div className="card status-card">
//         <div className="status-head">
//           <h3>Marketplace Round Status</h3>
//           <button className="refresh" onClick={refresh}>↻</button>
//         </div>

//         {error && <div className="error-msg">{error}</div>}

//         {/* ── Main stats ──────────────────────────────────────────────── */}
//         <div className="stats-grid">
//           <StatusItem label="Current Phase"      value={phase} />
//           <StatusItem label="Current Round"      value={round} />
//           <StatusItem label="Total Participants" value={total} />
//           <StatusItem label="Next Free Slot"     value={nextSlot} />
//           <StatusItem
//             label="Phase Time Remaining"
//             value={formatTime(liveTime ?? remainingTime)}
//           />
//         </div>

//         {/* ── Transfer Window ─────────────────────────────────────────── */}
//         <div className="transfer-window-section">
//           <h3>Energy Transfer Window</h3>

//           <div className="transfer-window-card">
//             <div className="transfer-window-row">

//               <div className="transfer-stat">
//                 <div className="stat-label">Status</div>
//                 <div className={`transfer-badge ${badgeClass}`}>
//                   {badgeLabel}
//                 </div>
//               </div>

//               <div className="transfer-stat">
//                 <div className="stat-label">Transfer Round</div>
//                 <div className="stat-value">
//                   {transferWindow?.transferRound ?? "-"}
//                 </div>
//               </div>

//               <div className="transfer-stat">
//                 <div className="stat-label">Time Remaining</div>
//                 <div className={`stat-value ${transferWindow?.isOpen ? "time-running" : "time-stopped"}`}>
//                   {transferWindow?.isOpen
//                     ? formatTime(liveTransferTime ?? transferWindow?.remainingSeconds)
//                     : "00:00"}
//                 </div>
//               </div>

//               <div className="transfer-stat">
//                 <div className="stat-label">Closes At</div>
//                 <div className="stat-value">
//                   {transferWindow?.closesAt ?? "-"}
//                 </div>
//               </div>

//             </div>

//             {/* Message */}
//             <div className="transfer-message">
//               {transferWindow?.message ?? "Fetching transfer window info..."}
//             </div>
//           </div>
//         </div>

//         {/* ── Participants ─────────────────────────────────────────────── */}
//         <div className="participants-section">
//           <div className="participants-header">
//             <h3>Participants List</h3>
//             <button className="toggle-btn" onClick={() => setExpanded(!expanded)}>
//               {expanded ? "▲ Hide" : "▼ Show"}
//             </button>
//           </div>

//           {expanded && (
//             <>
//               {participants.length > 0 ? (
//                 <table className="participants-table">
//                   <thead>
//                     <tr>
//                       <th>Address</th>
//                       <th>Role</th>
//                       <th>Energy (kWh)</th>
//                       <th>Price (Rs)</th>
//                     </tr>
//                   </thead>
//                   <tbody>
//                     {participants.map((p, idx) => (
//                       <tr key={idx}>
//                         <td>{p[0]}</td>
//                         <td>{p[1] === 1 ? "Buyer" : p[1] === 2 ? "Seller" : "N/A"}</td>
//                         <td>{(p[2] / 100).toFixed(0)}</td>
//                         <td>{(p[3] / 100).toFixed(0)}</td>
//                       </tr>
//                     ))}
//                   </tbody>
//                 </table>
//               ) : (
//                 <p>No participants found.</p>
//               )}
//             </>
//           )}
//         </div>

//         {/* ── Submitted Results ────────────────────────────────────────── */}
//         <div className="submitted-section">
//           <div className="participants-header">
//             <h3>Submitted Execution Results</h3>
//             <button className="toggle-btn" onClick={() => setShowResults(!showResults)}>
//               {showResults ? "▲ Hide" : "▼ Show"}
//             </button>
//           </div>

//           {showResults && (
//             <>
//               {submittedResults.length > 0 ? (
//                 <table className="participants-table">
//                   <thead>
//                     <tr>
//                       <th>#</th>
//                       <th>Submitter</th>
//                       <th>Result Hash</th>
//                     </tr>
//                   </thead>
//                   <tbody>
//                     {submittedResults.map((r, idx) => (
//                       <tr key={idx}>
//                         <td>{idx + 1}</td>
//                         <td>{r.submitter}</td>
//                         <td className="hash-cell">{r.resultHash}</td>
//                       </tr>
//                     ))}
//                   </tbody>
//                 </table>
//               ) : (
//                 <p>No submitted results found.</p>
//               )}
//             </>
//           )}
//         </div>

//       </div>
//     </div>
//   );
// };

// export default StatusPanel;


import React, { useEffect, useState } from "react";
import {
  getCurrentPhase,
  getCurrentRound,
  getTotalParticipants,
  getNextAvailableSlot,
  getParticipantsList,
  getSubmittedResults,
  getRemainingTimeInPhase,
  getEnergyTransferingTime,
} from "../../api/api";
import "./StatusPanel.css";

const StatusItem = ({ label, value }) => (
  <div className="stat">
    <div className="stat-label">{label}</div>
    <div className="stat-value">{value}</div>
  </div>
);

const StatusPanel = () => {
  const [phase, setPhase]                           = useState("-");
  const [round, setRound]                           = useState("-");
  const [total, setTotal]                           = useState("-");
  const [nextSlot, setNextSlot]                     = useState("-");
  const [participants, setParticipants]             = useState([]);
  const [submittedResults, setSubmittedResults]     = useState([]);
  const [expanded, setExpanded]                     = useState(false);
  const [showResults, setShowResults]               = useState(false);
  const [error, setError]                           = useState("");
  const [remainingTime, setRemainingTime]           = useState("-");
  const [liveTime, setLiveTime]                     = useState(null);
  const [transferWindow, setTransferWindow]         = useState(null);
  const [liveTransferTime, setLiveTransferTime]     = useState(null);

  // ─── Fetch all data ──────────────────────────────────────────────────────
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
        getEnergyTransferingTime(),
      ]);

      const [
        phaseRes,
        roundRes,
        totalRes,
        slotRes,
        participantsRes,
        submittedRes,
        remainingTimeRes,
        energyTransferTimeRes,
      ] = results;

      if (phaseRes.status === "fulfilled")
        setPhase(phaseRes.value.currentPhase ?? "-");

      if (roundRes.status === "fulfilled")
        setRound(roundRes.value.currentRound ?? "-");

      if (totalRes.status === "fulfilled")
        setTotal(totalRes.value.TOTAL_PARTICIPANTS ?? "-");

      if (slotRes.status === "fulfilled")
        setNextSlot(slotRes.value.nextAvailableSlot ?? "-");

      if (participantsRes.status === "fulfilled")
        setParticipants(participantsRes.value.participantsList ?? []);

      if (submittedRes.status === "fulfilled")
        setSubmittedResults(submittedRes.value.submittedResults ?? []);

      // ── Phase time: NEVER reset upward ──────────────────────────────────
      if (remainingTimeRes.status === "fulfilled") {
        const serverTime = remainingTimeRes.value?.remainingTimeInPhase ?? "-";
        setRemainingTime(serverTime);

        if (typeof serverTime === "number") {
          setLiveTime((prev) => {
            if (prev === null) return serverTime;       // first load — always set
            if (serverTime > prev) return prev;         // server higher → ignore, keep counting down
            if ((prev - serverTime) > 5) return serverTime;  // local drifted too low → resync
            return prev;                                // within 5s tolerance → keep local
          });
        } else {
          setLiveTime(null);
        }
      }

      // ── Transfer window: NEVER reset upward ─────────────────────────────
      if (energyTransferTimeRes.status === "fulfilled") {
        const tw = energyTransferTimeRes.value;
        setTransferWindow(tw);  // ← always update the window metadata

        const serverTransfer = tw?.remainingSeconds ?? null;

        if (tw?.isOpen && typeof serverTransfer === "number") {
          setLiveTransferTime((prev) => {
            if (prev === null) return serverTransfer;       // first load
            if (serverTransfer > prev) return prev;         // server higher → ignore
            if ((prev - serverTransfer) > 5) return serverTransfer;  // drifted → resync
            return prev;                                    // keep local
          });
        } else {
          setLiveTransferTime(null);  // window closed or not started
        }
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

  // ⏱️ Phase countdown every 1 sec
  useEffect(() => {
    const timer = setInterval(() => {
      setLiveTime((prev) => {
        if (prev === null || prev <= 0) return prev;
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // ⏱️ Transfer window countdown every 1 sec
  useEffect(() => {
    const timer = setInterval(() => {
      setLiveTransferTime((prev) => {
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
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // ── Transfer window badge ────────────────────────────────────────────────
  const transferBadge = () => {
    if (!transferWindow) return { label: "-", className: "badge-idle" };

    switch (transferWindow.status) {
      case "not_started":
        return { label: "Not Started", className: "badge-idle" };
      case "open":
        return {
          label:
            transferWindow.transferRound < transferWindow.currentRound
              ? `Round ${transferWindow.transferRound} Overlap`
              : "Open",
          className: "badge-open",
        };
      case "closed":
        return { label: "Closed", className: "badge-closed" };
      default:
        return { label: "-", className: "badge-idle" };
    }
  };

  const { label: badgeLabel, className: badgeClass } = transferBadge();

  return (
    <div className="status-center">
      <div className="card status-card">
        <div className="status-head">
          <h3>Marketplace Round Status</h3>
          <button className="refresh" onClick={refresh}>↻</button>
        </div>

        {error && <div className="error-msg">{error}</div>}

        {/* ── Main stats ───────────────────────────────────────────────── */}
        <div className="stats-grid">
          <StatusItem label="Current Phase"      value={phase} />
          <StatusItem label="Current Round"      value={round} />
          <StatusItem label="Total Participants" value={total} />
          <StatusItem label="Next Free Slot"     value={nextSlot} />
          <StatusItem
            label="Phase Time Remaining"
            value={formatTime(liveTime)}
          />
        </div>

        {/* ── Transfer Window ──────────────────────────────────────────── */}
        <div className="transfer-window-section">
          <h3>Energy Transfer Window</h3>

          <div className="transfer-window-card">
            <div className="transfer-window-row">

              <div className="transfer-stat">
                <div className="stat-label">Status</div>
                <div className={`transfer-badge ${badgeClass}`}>
                  {badgeLabel}
                </div>
              </div>

              <div className="transfer-stat">
                <div className="stat-label">Transfer Round</div>
                <div className="stat-value">
                  {transferWindow?.transferRound ?? "-"}
                </div>
              </div>

              <div className="transfer-stat">
                <div className="stat-label">Time Remaining</div>
                <div className={`stat-value ${transferWindow?.isOpen ? "time-running" : "time-stopped"}`}>
                  {transferWindow?.isOpen
                    ? formatTime(liveTransferTime)
                    : "00:00"}
                </div>
              </div>

              <div className="transfer-stat">
                <div className="stat-label">Closes At</div>
                <div className="stat-value">
                  {transferWindow?.closesAt ?? "-"}
                </div>
              </div>

            </div>

            <div className="transfer-message">
              {transferWindow?.message ?? "Fetching transfer window info..."}
            </div>
          </div>
        </div>

        {/* ── Participants ─────────────────────────────────────────────── */}
        <div className="participants-section">
          <div className="participants-header">
            <h3>Participants List</h3>
            <button className="toggle-btn" onClick={() => setExpanded(!expanded)}>
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
                        <td>{p[1] === 1 ? "Buyer" : p[1] === 2 ? "Seller" : "N/A"}</td>
                        <td>{(p[2] / 1000).toPrecision(3)}</td>
                        <td>{(p[3] / 1000).toPrecision(3)}</td>
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

        {/* ── Submitted Results ────────────────────────────────────────── */}
        <div className="submitted-section">
          <div className="participants-header">
            <h3>Submitted Execution Results</h3>
            <button className="toggle-btn" onClick={() => setShowResults(!showResults)}>
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