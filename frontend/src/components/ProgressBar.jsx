// frontend/src/components/ProgressBar.jsx
import React from "react";

export default function ProgressBar({ value = 0 }) {
  const pct = Math.max(0, Math.min(1, Number.isFinite(value) ? value : 0));
  return (
    <div
      style={{
        width: "100%",
        height: 10,
        borderRadius: 999,
        background: "#1b1e2c",
        border: "1px solid var(--border)",
        overflow: "hidden",
      }}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(pct * 100)}
      role="progressbar"
    >
      <div
        style={{
          width: `${pct * 100}%`,
          height: "100%",
          background:
            "linear-gradient(90deg, rgba(42,114,255,1), rgba(94,210,255,1))",
          transition: "width 260ms ease",
        }}
      />
    </div>
  );
}
