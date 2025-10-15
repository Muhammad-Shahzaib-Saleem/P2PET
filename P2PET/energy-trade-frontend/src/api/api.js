// src/api/api.js
import axios from "axios";

// Auto-detect host (works when you open UI from another device on LAN)
const host = window.location.hostname;
// Prefer .env override: VITE_API_BASE=http://<pi-ip>:8000
export const API_BASE = "http://192.168.0.141:8000";

// Shared axios instance (you can add interceptors/logging here later)
const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
});

// ---- Transactions / Actions ----
export const registerParticipant = async () => {
  const { data } = await api.post("/register");
  return data;
};

export const submitTrade = async ({ role, energy, price }) => {
  const params = { role, energy: Number(energy), price: Number(price) };
  // Your FastAPI /submit-data expects query/body fields role, energy, price
  const { data } = await api.post("/submit-data", null, { params });
  return data;
};

export const advancePhase = async () => {
  const { data } = await api.post("/advance-phase");
  return data;
};

export const hashParticipants = async () => {
  const { data } = await api.post("/hash-participants");
  return data;
};

export const submitExecutionResult = async () => {
  const { data } = await api.post("/submit-execution-result");
  return data;
};

export const verifyExecution = async () => {
  const { data } = await api.post("/verify-execution");
  return data;
};

// ---- Reads / Status ----
export const getCurrentPhase = async () => {
  const { data } = await api.get("/current-phase");
  return data;
};

export const getCurrentRound = async () => {
  const { data } = await api.get("/current-round");
  return data;
};

export const getTotalParticipants = async () => {
  const { data } = await api.get("/total-participants");
  return data;
};

export const getNextAvailableSlot = async () => {
  const { data } = await api.get("/next-available-slot");
  return data;
};

export const getParticipantsList = async () => {
  const { data } = await api.get("/participants-list");
  return data;
};
