import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import SimilarCasesList from "./SimilarCasesList";

const SAMPLE = [
  {
    ticket_id: "TKT-001",
    title: "VPN-Zugang defekt",
    final_department: "Bank-IT Support",
    final_category: "support",
    final_team: "network-team",
    similarity_score: 0.85,
  },
  {
    ticket_id: "TKT-002",
    title: "Passwort-Reset SAP",
    final_department: "IT-User-Services",
    final_category: "support",
    final_team: null,
    similarity_score: 0.42,
  },
];

function renderWithRouter(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe("SimilarCasesList", () => {
  it("returns null when no cases are provided", () => {
    const { container } = renderWithRouter(<SimilarCasesList cases={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders one row per case with department, team and rounded similarity", () => {
    renderWithRouter(<SimilarCasesList cases={SAMPLE} />);

    expect(screen.getByText(/VPN-Zugang defekt/)).toBeInTheDocument();
    expect(screen.getByText(/85%/)).toBeInTheDocument();
    expect(screen.getByText(/42%/)).toBeInTheDocument();
    // Team only shown when provided
    expect(screen.getByText(/network-team/)).toBeInTheDocument();
  });

  it("calls onNavigate with the ticket id when a row is clicked", async () => {
    const onNavigate = vi.fn();
    renderWithRouter(<SimilarCasesList cases={SAMPLE} onNavigate={onNavigate} />);

    await userEvent.click(screen.getByTitle(/TKT-001/));

    expect(onNavigate).toHaveBeenCalledWith("TKT-001");
  });
});
