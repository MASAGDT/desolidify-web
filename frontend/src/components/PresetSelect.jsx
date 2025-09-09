// frontend/src/components/PresetSelect.jsx
import React from "react";

export default function PresetSelect({ presets = {}, value, onChange }) {
  const names = Object.keys(presets || {});
  return (
    <div className="row">
      <select
        className="input"
        value={value || ""}
        onChange={(e) => onChange?.(e.target.value)}
      >
        {!value && <option value="">— Select a preset —</option>}
        {names.map((n) => (
          <option key={n} value={n}>
            {n}
          </option>
        ))}
      </select>
    </div>
  );
}
