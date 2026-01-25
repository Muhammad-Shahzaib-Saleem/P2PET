// src/api/chatbot.js
import axios from "axios";
import { API_BASE } from "./api";

const chatApi = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 minutes for AI responses
});

/**
 * Send a message to the AI chatbot
 * @param {Array} messages - Array of {role: "user"|"assistant", content: string}
 * @returns {Promise<{response: string, status: string}>}
 */
export const sendChatMessage = async (messages) => {
  try {
    const { data } = await chatApi.post("/chat", { messages });
    return data;
  } catch (err) {
    const errorDetail = err.response?.data?.detail || err.message;
    throw new Error(errorDetail);
  }
};

/**
 * Check if chatbot is configured and ready
 * @returns {Promise<{status: string, message: string}>}
 */
export const checkChatbotHealth = async () => {
  try {
    const { data } = await chatApi.get("/chat/health");
    return data;
  } catch (err) {
    return { status: "error", message: err.message };
  }
};

