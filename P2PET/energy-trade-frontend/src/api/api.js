// src/api/api.js
import axios from "axios";

// Auto-detect host (works when you open UI from another device on LAN)
const host = window.location.hostname;
// Prefer .env override: VITE_API_BASE=http://<pi-ip>:8000
export const API_BASE = "http://localhost:8000/";

// Shared axios instance (you can add interceptors/logging here later)
const api = axios.create({
  baseURL: API_BASE,
  timeout: 300000,
});

// ---- Transactions / Actions ----
export const registerParticipant = async ({ hostname }) => {
  const params = {
    hostname,
  };

  const { data } = await api.post("/dynamic_register", null, { params });
  return data;
};

export const submitTrade = async ({ hostname, role, energy, price }) => {
  const params = {
    hostname,
    role,
    energy: Number(energy),
    price: Number(price),
  };
  // Your FastAPI /submit-data expects query/body fields role, energy, price
  const { data } = await api.post("/dynamic_submit_data", null, { params });
  return data;
};

export const advancePhase = async ({ hostname }) => {
  const params = {
    hostname,
  };

  const { data } = await api.post("/dynamic_advance_phase", null, { params });
  return data;
};

export const hashParticipants = async ({ hostname }) => {
  const params = {
    hostname,
  };
  const { data } = await api.post("/dynamic_hash_participants", null, {
    params,
  });
  return data;
};

export const submitExecutionResult = async ({ hostname }) => {
  const params = {
    hostname,
  };
  const { data } = await api.post("/dynamic_submit_execution_result", null, {
    params,
  });
  return data;
};

export const verifyExecution = async ({ hostname }) => {
  const params = {
    hostname,
  };

  const { data } = await api.post("/dynamic_verify_execution", null, {
    params,
  });
  return data;
};

// ---- Reads / Status ----
export const getCurrentPhase = async () => {
  const { data } = await api.get("/current_phase");
  return data;
};

export const getCurrentRound = async () => {
  const { data } = await api.get("/current_round");
  return data;
};

export const getTotalParticipants = async () => {
  const { data } = await api.get("/total_participants");
  return data;
};

export const getNextAvailableSlot = async () => {
  const { data } = await api.get("/next_available_slot");
  return data;
};

export const getParticipantsList = async () => {
  const { data } = await api.get("/participants_list");
  return data;
};

export const getSubmittedResults = async () => {
  const { data } = await api.get("/submitted_results");
  return data;
};
