"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const [connecting, setConnecting] = useState(false);
  const router = useRouter();

  const handleConnect = () => {
    setConnecting(true);
    router.push("/session");
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      {/* Logo / Branding */}
      <div className="mb-12 text-center">
        <div className="relative mx-auto mb-6 h-24 w-24">
          <div className="absolute inset-0 rounded-full bg-kira-500/20 animate-pulse-slow" />
          <div className="absolute inset-2 rounded-full bg-kira-500/40" />
          <div className="absolute inset-4 rounded-full bg-kira-500 flex items-center justify-center">
            <span className="text-2xl font-bold text-white">K</span>
          </div>
        </div>
        <h1 className="text-4xl font-bold text-foreground">Kira</h1>
        <p className="mt-2 text-lg text-gray-400">
          Assistente AI Personale
        </p>
      </div>

      {/* Connect Button */}
      <button
        onClick={handleConnect}
        disabled={connecting}
        className={`
          rounded-full px-8 py-4 text-lg font-medium text-white
          transition-all duration-300
          ${
            connecting
              ? "bg-kira-600/50 cursor-wait"
              : "bg-kira-600 hover:bg-kira-700 hover:shadow-lg hover:shadow-kira-500/25 active:scale-95"
          }
        `}
      >
        {connecting ? "Connessione..." : "Parla con Kira"}
      </button>

      {/* Footer */}
      <p className="mt-16 text-xs text-gray-500">
        Powered by LiveKit + Agno + Claude
      </p>
    </main>
  );
}
