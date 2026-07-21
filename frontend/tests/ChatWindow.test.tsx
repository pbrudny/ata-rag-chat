import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ChatWindow } from "../components/ChatWindow";
import * as sseClient from "../lib/sseClient";
import type { ChatSSEEvent } from "../lib/types";

function mockStream(events: ChatSSEEvent[]) {
  return vi
    .spyOn(sseClient, "streamChat")
    .mockImplementation(async (_options, onEvent) => {
      for (const event of events) {
        onEvent(event);
      }
    });
}

describe("ChatWindow", () => {
  it("renders the streamed answer with citations and confidence", async () => {
    mockStream([
      {
        event: "sources",
        data: [{ title: "Rekrutacja", url: "https://akademiata.pl/r", section: null }],
      },
      { event: "token", data: "Rekrutacja " },
      { event: "token", data: "trwa do wrzesnia." },
      { event: "done", data: { confidence: 0.82, answered: true } },
    ]);

    render(<ChatWindow />);

    fireEvent.change(screen.getByPlaceholderText(/AkademiaTA/i), {
      target: { value: "Kiedy jest rekrutacja?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /wyslij|send/i }));

    expect(screen.getByText("Kiedy jest rekrutacja?")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Rekrutacja trwa do wrzesnia.")).toBeInTheDocument();
    });
    expect(screen.getByRole("link", { name: "Rekrutacja" })).toHaveAttribute(
      "href",
      "https://akademiata.pl/r"
    );
    expect(screen.getByText(/Confidence: 82%/)).toBeInTheDocument();
  });

  it("renders the fallback message without a confidence badge", async () => {
    mockStream([
      { event: "sources", data: [] },
      {
        event: "token",
        data: "Nie znalazlem tej informacji na stronie internetowej AkademiaTA.",
      },
      { event: "done", data: { confidence: 0.1, answered: false } },
    ]);

    render(<ChatWindow />);

    fireEvent.change(screen.getByPlaceholderText(/AkademiaTA/i), {
      target: { value: "Jaka jest pogoda?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /wyslij|send/i }));

    await waitFor(() => {
      expect(
        screen.getByText("Nie znalazlem tej informacji na stronie internetowej AkademiaTA.")
      ).toBeInTheDocument();
    });
    expect(screen.queryByText(/Confidence:/)).not.toBeInTheDocument();
  });

  it("switches placeholder and button copy when toggling language", () => {
    mockStream([]);
    render(<ChatWindow />);

    expect(screen.getByPlaceholderText("Zadaj pytanie o AkademiaTA...")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "EN" }));

    expect(screen.getByPlaceholderText("Ask a question about AkademiaTA...")).toBeInTheDocument();
  });

  it("does not submit an empty question", () => {
    const spy = mockStream([]);
    render(<ChatWindow />);

    fireEvent.click(screen.getByRole("button", { name: /wyslij|send/i }));

    expect(spy).not.toHaveBeenCalled();
  });
});
