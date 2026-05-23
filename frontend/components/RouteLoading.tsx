"use client";

import { useEffect, useState } from "react";

export default function RouteLoading() {
  const [pct, setPct] = useState(0);

  useEffect(() => {
    let frame: number;
    const start = performance.now();
    const duration = 1500;

    const tick = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 2);
      setPct(Math.floor(eased * 99));
      if (progress < 1) frame = requestAnimationFrame(tick);
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, []);

  return (
    <div className="relative min-h-[70vh] flex items-center justify-center font-mono select-none">
      <span className="absolute top-0 left-0 text-wc-muted text-3xl">/</span>
      <span className="absolute top-0 right-0 text-wc-muted text-3xl">&gt;</span>
      <span className="absolute bottom-0 left-0 text-wc-muted text-3xl">&copy;</span>
      <span className="absolute bottom-0 right-0 text-wc-muted text-3xl">]</span>

      <div className="text-center">
        <div className="text-7xl sm:text-8xl font-bold text-wc-gold tabular-nums tracking-tight">
          {String(pct).padStart(2, "0")}
          <span className="text-wc-muted">%</span>
        </div>
        <div className="mt-6 h-px w-48 mx-auto bg-wc-border overflow-hidden">
          <div
            className="h-full bg-wc-gold transition-[width] duration-100 ease-out"
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="mt-4 text-xs uppercase tracking-[0.4em] text-wc-muted animate-pulse">
          Loading
        </div>
      </div>
    </div>
  );
}
