"use client";

import { useEffect, useRef } from "react";

interface AuraVisualizerProps {
  state: string;
  audioTrack?: any;
}

export function AuraVisualizer({ state, audioTrack }: AuraVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d")!;
    const size = 280;
    canvas.width = size;
    canvas.height = size;

    let phase = 0;

    const draw = () => {
      ctx.clearRect(0, 0, size, size);
      phase += 0.02;

      const centerX = size / 2;
      const centerY = size / 2;

      // Determine intensity based on state
      const intensity =
        state === "speaking"
          ? 1.0
          : state === "thinking"
          ? 0.6
          : state === "listening"
          ? 0.4
          : 0.2;

      // Draw multiple concentric aura rings
      for (let ring = 3; ring >= 0; ring--) {
        const baseRadius = 40 + ring * 25;
        const radiusOscillation =
          Math.sin(phase + ring * 0.8) * 8 * intensity;
        const radius = baseRadius + radiusOscillation;

        const alpha = (0.15 - ring * 0.03) * (0.5 + intensity * 0.5);

        const gradient = ctx.createRadialGradient(
          centerX,
          centerY,
          radius * 0.3,
          centerX,
          centerY,
          radius
        );

        gradient.addColorStop(0, `rgba(99, 102, 241, ${alpha * 2})`);
        gradient.addColorStop(0.5, `rgba(129, 140, 248, ${alpha})`);
        gradient.addColorStop(1, `rgba(99, 102, 241, 0)`);

        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        ctx.fillStyle = gradient;
        ctx.fill();
      }

      // Inner core
      const coreGradient = ctx.createRadialGradient(
        centerX,
        centerY,
        0,
        centerX,
        centerY,
        35
      );
      coreGradient.addColorStop(0, "rgba(255, 255, 255, 0.9)");
      coreGradient.addColorStop(0.4, "rgba(199, 210, 254, 0.6)");
      coreGradient.addColorStop(1, "rgba(99, 102, 241, 0.2)");

      ctx.beginPath();
      ctx.arc(centerX, centerY, 35 + Math.sin(phase * 1.5) * 3 * intensity, 0, Math.PI * 2);
      ctx.fillStyle = coreGradient;
      ctx.fill();

      animationRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animationRef.current);
    };
  }, [state, audioTrack]);

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        className="rounded-full"
        style={{ width: 280, height: 280 }}
      />
      {/* State label inside the orb */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <span className="text-lg font-medium text-white/80">
          {state === "speaking"
            ? "♪"
            : state === "thinking"
            ? "..."
            : state === "listening"
            ? "●"
            : ""}
        </span>
      </div>
    </div>
  );
}
