// src/components/StatusPanel/StatusPanel.jsx
import React, { useEffect, useState } from "react";
import "./StatusPanel.css";
import {
  getCurrentPhase,
  getCurrentRound,
  getTotalParticipants,
  getNextAvailableSlot,
} from "../../api/api";

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

  const refresh = async () => {
    try {
      const [{ currentPhase }, { currentRound }, { TOTAL_PARTICIPANTS }, { nextAvailableSlot }] =
        await Promise.all([
          getCurrentPhase(),
          getCurrentRound(),
          getTotalParticipants(),
          getNextAvailableSlot(),
        ]);
      setPhase(currentPhase ?? "-");
      setRound(currentRound ?? "-");
      setTotal(TOTAL_PARTICIPANTS ?? "-");
      setNextSlot(nextAvailableSlot ?? "-");
    } catch (e) {
      console.error("Status refresh failed:", e);
    }
  };

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 5000); // auto-refresh
    return () => clearInterval(id);
  }, []);

  return (
    <div className="status-center">
      <div className="card status-card">
        <div className="status-head">
          <h3>Network / Round Status</h3>
          <button className="refresh" onClick={refresh} title="Refresh">↻</button>
        </div>
        <div className="stats-grid">
          <StatusItem label="Current Phase" value={phase} />
          <StatusItem label="Current Round" value={round} />
          <StatusItem label="Total Participants" value={total} />
          <StatusItem label="Next Free Slot" value={nextSlot} />
        </div>
      </div>
    </div>
  );
};

export default StatusPanel;


// // src/components/StatusPanel/StatusPanel.jsx
// import React, { useEffect, useState } from "react";
// import "./StatusPanel.css";
// import {
//   getCurrentPhase,
//   getCurrentRound,
//   getTotalParticipants,
//   getNextAvailableSlot,
// } from "../../api/api";

// const StatusItem = ({ label, value }) => (
//   <div className="stat">
//     <div className="stat-label">{label}</div>
//     <div className="stat-value">{value}</div>
//   </div>
// );

// const StatusPanel = () => {
//   const [phase, setPhase] = useState("-");
//   const [round, setRound] = useState("-");
//   const [total, setTotal] = useState("-");
//   const [nextSlot, setNextSlot] = useState("-");

//   const refresh = async () => {
//     try {
//       const [{ currentPhase }, { currentRound }, { TOTAL_PARTICIPANTS }, { nextAvailableSlot }] =
//         await Promise.all([
//           getCurrentPhase(),
//           getCurrentRound(),
//           getTotalParticipants(),
//           getNextAvailableSlot(),
//         ]);
//       setPhase(currentPhase ?? "-");
//       setRound(currentRound ?? "-");
//       setTotal(TOTAL_PARTICIPANTS ?? "-");
//       setNextSlot(nextAvailableSlot ?? "-");
//     } catch (e) {
//       console.error("Status refresh failed:", e);
//     }
//   };

//   useEffect(() => {
//     refresh();
//     const id = setInterval(refresh, 5000); // auto-refresh
//     return () => clearInterval(id);
//   }, []);

//   return (
//     <div className="card status-card">
//       <div className="status-head">
//         <h3>Network / Round Status</h3>
//         <button className="refresh" onClick={refresh} title="Refresh">↻</button>
//       </div>
//       <div className="stats-grid">
//         <StatusItem label="Current Phase" value={phase} />
//         <StatusItem label="Current Round" value={round} />
//         <StatusItem label="Total Participants" value={total} />
//         <StatusItem label="Next Free Slot" value={nextSlot} />
//       </div>
//     </div>
//   );
// };

// export default StatusPanel;
