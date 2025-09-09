// frontend/src/components/ParamSliders.jsx
import React, { useMemo, useState } from "react";
import Tooltip from "./Tooltip.jsx";

function NumRow({ k, spec, value, onChange }) {
  const step = spec.step ?? (spec.type === "integer" ? 1 : 0.1);
  const min = spec.min ?? 0;
  const max = spec.max ?? 100;
  const v = value ?? spec.default ?? min;

  return (
    <div style={{ marginBottom: 10 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <label htmlFor={`param-${k}`} style={{ fontSize: 12 }}>
          {k} <Tooltip text={spec.tip} />
        </label>
        <input
          className="input"
          style={{ width: 110, textAlign: "right" }}
          id={`param-${k}-num`}
          type="number"
          step={step}
          min={min}
          max={max}
          value={v ?? ""}
          onChange={(e) =>
            onChange({ [k]: e.target.value === "" ? null : Number(e.target.value) })
          }
        />
      </div>
      <input
        id={`param-${k}`}
        type="range"
        min={min}
        max={max}
        step={step}
        value={Number.isFinite(v) ? v : min}
        onChange={(e) => onChange({ [k]: Number(e.target.value) })}
        style={{ width: "100%" }}
      />
    </div>
  );
}

function BoolRow({ k, spec, value, onChange }) {
  const v = !!(value ?? spec.default);
  return (
    <div className="row" style={{ marginBottom: 10 }}>
      <label htmlFor={`param-${k}`} style={{ fontSize: 12 }}>
        {k} <Tooltip text={spec.tip} />
      </label>
      <div style={{ flex: 1 }} />
      <input
        id={`param-${k}`}
        type="checkbox"
        checked={v}
        onChange={(e) => onChange({ [k]: !!e.target.checked })}
      />
    </div>
  );
}

function SelectRow({ k, spec, value, onChange }) {
  const v = (value ?? spec.default) || "";
  return (
    <div className="row" style={{ marginBottom: 10 }}>
      <label htmlFor={`param-${k}`} style={{ fontSize: 12 }}>
        {k} <Tooltip text={spec.tip} />
      </label>
      <div style={{ flex: 1 }} />
      <select
        id={`param-${k}`}
        className="input"
        style={{ width: 180 }}
        value={v}
        onChange={(e) => onChange({ [k]: e.target.value })}
      >
        {(spec.choices || []).map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
    </div>
  );
}

export default function ParamSliders({ specs = {}, values = {}, onChange }) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const entries = useMemo(() => Object.entries(specs), [specs]);
  const mainKeys = useMemo(
    () =>
      entries
        .map(([k]) => k)
        .filter((k) => !["chunk", "mem_delay", "mem_tries"].includes(k)),
    [entries]
  );
  const advancedKeys = useMemo(
    () => ["chunk", "mem_delay", "mem_tries"].filter((k) => specs[k]),
    [specs]
  );

  const renderRow = (k) => {
    const spec = specs[k] || {};
    const type = spec.type || "number";
    const v = values[k];

    if (type === "bool") return <BoolRow key={k} k={k} spec={spec} value={v} onChange={onChange} />;
    if (type === "select") return <SelectRow key={k} k={k} spec={spec} value={v} onChange={onChange} />;
    return <NumRow key={k} k={k} spec={spec} value={v} onChange={onChange} />;
  };

  return (
    <div>
      {mainKeys.map(renderRow)}

      {advancedKeys.length > 0 && (
        <>
          <div className="row" style={{ marginTop: 6, marginBottom: 6 }}>
            <div style={{ fontSize: 12, color: "var(--muted)" }}>Advanced</div>
            <div style={{ flex: 1 }} />
            <button
              className="btn ghost"
              type="button"
              onClick={() => setShowAdvanced((s) => !s)}
            >
              {showAdvanced ? "Hide" : "Show"}
            </button>
          </div>
          {showAdvanced && advancedKeys.map(renderRow)}
        </>
      )}
    </div>
  );
}
