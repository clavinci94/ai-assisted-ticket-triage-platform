import axios from "axios";

import { invalidate, swr } from "./swrCache";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
});

// ---------------------------------------------------------------------
// Read endpoints — go through the stale-while-revalidate cache so
// switching between Übersicht / Workbench / Reports doesn't refire
// the same query against a (potentially cold) database every time.
// ---------------------------------------------------------------------

export async function fetchTickets() {
  return swr(
    "tickets:list",
    async () => (await api.get("/tickets")).data,
    { ttlMs: 30_000 },
  );
}

export async function fetchTicketWorkbench(params = {}) {
  const key = `tickets:workbench:${JSON.stringify(params)}`;
  return swr(
    key,
    async () => (await api.get("/tickets/workbench", { params })).data,
    { ttlMs: 15_000 },
  );
}

export async function fetchTicket(ticketId) {
  // Ticket detail is the entry point for editing; bypass the cache so
  // reviewers always see the freshest state when opening a ticket.
  const response = await api.get(`/tickets/${ticketId}`);
  return response.data;
}

export async function fetchDashboardAnalytics() {
  return swr(
    "tickets:analytics",
    async () => (await api.get("/tickets/analytics")).data,
    { ttlMs: 30_000 },
  );
}

// ---------------------------------------------------------------------
// Mutations — invalidate every read-cache they could affect.
// ---------------------------------------------------------------------

function invalidateTicketReads() {
  invalidate((key) => key.startsWith("tickets:"));
}

export async function triageTicket(payload) {
  const response = await api.post("/tickets/triage/llm", payload);
  invalidateTicketReads();
  return response.data;
}

export async function previewTriageTicket(payload) {
  // Preview doesn't persist anything — no cache to drop.
  const response = await api.post("/tickets/triage/llm/preview", payload);
  return response.data;
}

export async function saveDecision(payload) {
  const response = await api.post("/tickets/decision", payload);
  invalidateTicketReads();
  return response.data;
}

export async function assignTicket(payload) {
  const response = await api.post("/tickets/assign", payload);
  invalidateTicketReads();
  return response.data;
}

export async function updateTicketStatus(payload) {
  const response = await api.post("/tickets/status", payload);
  invalidateTicketReads();
  return response.data;
}

export async function addTicketComment(payload) {
  const response = await api.post("/tickets/comments", payload);
  invalidateTicketReads();
  return response.data;
}

export async function escalateTicket(payload) {
  const response = await api.post("/tickets/escalate", payload);
  invalidateTicketReads();
  return response.data;
}
