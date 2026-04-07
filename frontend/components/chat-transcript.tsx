"use client";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ChatTranscriptProps {
  messages: Message[];
  agentState: string;
}

export function ChatTranscript({ messages, agentState }: ChatTranscriptProps) {
  if (messages.length === 0 && agentState !== "thinking") {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6 text-center">
        <p className="text-sm text-gray-500">
          La trascrizione della conversazione apparirà qui.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-xl border border-gray-800 bg-gray-900/50 p-4">
      {messages.map((msg, i) => (
        <div
          key={i}
          className={`flex ${
            msg.role === "user" ? "justify-end" : "justify-start"
          }`}
        >
          <div
            className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
              msg.role === "user"
                ? "bg-kira-600 text-white"
                : "bg-gray-800 text-gray-200"
            }`}
          >
            {msg.content}
          </div>
        </div>
      ))}

      {/* Thinking indicator */}
      {agentState === "thinking" && (
        <div className="flex justify-start">
          <div className="rounded-2xl bg-gray-800 px-4 py-2">
            <div className="flex space-x-1">
              <div className="h-2 w-2 rounded-full bg-kira-400 animate-bounce [animation-delay:-0.3s]" />
              <div className="h-2 w-2 rounded-full bg-kira-400 animate-bounce [animation-delay:-0.15s]" />
              <div className="h-2 w-2 rounded-full bg-kira-400 animate-bounce" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
