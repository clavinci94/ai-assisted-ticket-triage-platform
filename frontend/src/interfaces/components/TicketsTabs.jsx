import Tabs from "./Tabs";

const TICKET_VIEWS = [
  { to: "/tickets", label: "Alle", end: true },
  { to: "/tickets/mine", label: "Meine", end: true },
  { to: "/tickets/open", label: "Offene", end: true },
  { to: "/tickets/escalations", label: "Eskalationen", end: true },
];

export default function TicketsTabs() {
  return <Tabs items={TICKET_VIEWS} ariaLabel="Ticket-Ansichten" />;
}
