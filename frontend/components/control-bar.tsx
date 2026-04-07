"use client";

import {
  useLocalParticipant,
  TrackToggle,
  DisconnectButton,
} from "@livekit/components-react";
import { Track } from "livekit-client";

interface ControlBarProps {
  isChatOpen: boolean;
  onToggleChat: () => void;
}

export function ControlBar({ isChatOpen, onToggleChat }: ControlBarProps) {
  return (
    <div className="flex items-center justify-center gap-4">
      {/* Microphone Toggle */}
      <TrackToggle
        source={Track.Source.Microphone}
        className="rounded-full bg-kira-600 p-4 text-white transition-all hover:bg-kira-700 active:scale-95 data-[enabled=false]:bg-red-600"
      />

      {/* Chat Toggle */}
      <button
        onClick={onToggleChat}
        className={`rounded-full p-4 transition-all active:scale-95 ${
          isChatOpen
            ? "bg-gray-700 text-white"
            : "bg-gray-800 text-gray-400 hover:text-white"
        }`}
        title={isChatOpen ? "Nascondi chat" : "Mostra chat"}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      </button>

      {/* Disconnect */}
      <DisconnectButton className="rounded-full bg-red-600 p-4 text-white transition-all hover:bg-red-700 active:scale-95">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M18 6 6 18" />
          <path d="m6 6 12 12" />
        </svg>
      </DisconnectButton>
    </div>
  );
}
