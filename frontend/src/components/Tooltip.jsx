// frontend/src/components/Tooltip.jsx
import React from "react";

export default function Tooltip({ text }) {
  if (!text) return null;
  return (
    <span
      title={text}
      aria-label={text}
      style={{
        display: "inline-block",
        marginLeft: 6,
        color: "var(--muted)",
        background: "#2a2e45",
        borderRadius: 6,
        padding: "0 6px",
        fontSize: 10,
        lineHeight: "16px",
        verticalAlign: "middle",
      }}
    >
      ?
    </span>
  );
}
