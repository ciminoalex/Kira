"use client";

import { useCallback, useEffect, useState } from "react";
import {
  LiveKitRoom,
  useVoiceAssistant,
  RoomAudioRenderer,
  DisconnectButton,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { AuraVisualizer } from "@/components/aura-visualizer";
import { ChatTranscript } from "@/components/chat-transcript";
import { ControlBar } from "@/components/control-bar";

export default function SessionPage() {
  const [token, setToken] = useState<string>("");
  const [serverUrl, setServerUrl] = useState<string>("");

  useEffect(() => {
    // Fetch token from API
    fetch("/api/token")
      .then((res) => res.json())
      .then((data) => {
        setToken(data.token);
        setServerUrl(data.serverUrl);
      })
      .catch(console.error);
  }, []);

  if (!token || !serverUrl) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-kira-500 border-t-transparent" />
          <p className="text-gray-400">Connessione a Kira...</p>
        </div>
      </div>
    );
  }

  return (
    <LiveKitRoom
      token={token}
      serverUrl={serverUrl}
      connect={true}
      audio={true}
      className="flex min-h-screen flex-col"
    >
      <KiraSession />
      <RoomAudioRenderer />
    </LiveKitRoom>
  );
}

function KiraSession() {
  const { state, audioTrack } = useVoiceAssistant();
  const [messages, setMessages] = useState<
    Array<{ role: "user" | "assistant"; content: string; timestamp: Date }>
  >([]);
  const [isChatOpen, setIsChatOpen] = useState(true);

  const statusText = (() => {
    switch (state) {
      case "listening":
        return "Ti ascolto...";
      case "thinking":
        return "Sto pensando...";
      case "speaking":
        return "Sto parlando...";
      default:
        return "Premi il microfono per parlare";
    }
  })();

  return (
    <div className="flex flex-1 flex-col items-center justify-between p-4">
      {/* Header */}
      <header className="w-full max-w-2xl text-center py-4">
        <h1 className="text-2xl font-semibold text-foreground">Kira</h1>
        <p className="mt-1 text-sm text-gray-400">{statusText}</p>
      </header>

      {/* Visualizer */}
      <div className="flex-1 flex items-center justify-center">
        <AuraVisualizer state={state} audioTrack={audioTrack} />
      </div>

      {/* Chat Transcript */}
      {isChatOpen && (
        <div className="w-full max-w-2xl mb-4 max-h-[35vh] overflow-y-auto">
          <ChatTranscript messages={messages} agentState={state} />
        </div>
      )}

      {/* Controls */}
      <div className="w-full max-w-2xl pb-4">
        <ControlBar
          isChatOpen={isChatOpen}
          onToggleChat={() => setIsChatOpen(!isChatOpen)}
        />
      </div>
    </div>
  );
}
