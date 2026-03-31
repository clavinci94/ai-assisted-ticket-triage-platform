import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
});

export async function fetchTickets() {
  const response = await api.get("/tickets");
  return response.data;
}

export async function fetchTicketWorkbench(params = {}) {
  const response = await api.get("/tickets/workbench", { params });
  return response.data;
}

export async function fetchTicket(ticketId) {
  const response = await api.get(`/tickets/${ticketId}`);
  return response.data;
}

export async function triageTicket(payload) {
  const response = await api.post("/tickets/triage/llm", payload);
  return response.data;
}

export async function previewTriageTicket(payload) {
  const response = await api.post("/tickets/triage/llm/preview", payload);
  return response.data;
}

export async function saveDecision(payload) {
  const response = await api.post("/tickets/decision", payload);
  return response.data;
}

export async function assignTicket(payload) {
  const response = await api.post("/tickets/assign", payload);
  return response.data;
}

export async function updateTicketStatus(payload) {
  const response = await api.post("/tickets/status", payload);
  return response.data;
}

export async function addTicketComment(payload) {
  const response = await api.post("/tickets/comments", payload);
  return response.data;
}

export async function escalateTicket(payload) {
  const response = await api.post("/tickets/escalate", payload);
  return response.data;
}

export async function fetchDashboardAnalytics() {
  const response = await api.get("/tickets/analytics");
  return response.data;
}
