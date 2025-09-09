// frontend/src/components/UploadPanel.jsx
import React, { useCallback, useRef, useState } from "react";

export default function UploadPanel({
  file,
  onFileSelected,
  onStartPreview,
  onStartJob,
  disabled,
}) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  const openPicker = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const onChange = useCallback(
    (e) => {
      const f = e.target.files?.[0];
      if (f) onFileSelected(f);
    },
    [onFileSelected]
  );

  const onDrop = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      setDragOver(false);
      const f = e.dataTransfer.files?.[0];
      if (f) onFileSelected(f);
    },
    [onFileSelected]
  );

  const onDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragOver(true);
    if (e.type === "dragleave") setDragOver(false);
  }, []);

  function prettySize(n) {
    if (!Number.isFinite(n)) return "—";
    const u = ["B", "KB", "MB", "GB"];
    let i = 0;
    while (n >= 1024 && i < u.length - 1) {
      n /= 1024;
      i++;
    }
    return `${n.toFixed(1)} ${u[i]}`;
  }

  return (
    <div className="card">
      <h3 className="card-title">Upload STL</h3>
      <div
        className="uploader"
        onDragEnter={onDrag}
        onDragOver={onDrag}
        onDragLeave={onDrag}
        onDrop={onDrop}
        style={{
          border: "1px dashed var(--border)",
          borderRadius: 12,
          padding: 16,
          background: dragOver ? "#191c2b" : "#141726",
          cursor: "pointer",
        }}
        onClick={openPicker}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".stl,model/stl"
          onChange={onChange}
          hidden
        />
        {!file ? (
          <div style={{ textAlign: "center", color: "var(--muted)" }}>
            <div style={{ fontSize: 13, marginBottom: 6 }}>
              Drag &amp; drop an <strong>.stl</strong> file here
            </div>
            <div style={{ fontSize: 12 }}>or click to browse</div>
          </div>
        ) : (
          <div className="kv">
            <div>File</div>
            <div style={{ textAlign: "right" }}>{file.name}</div>
            <div>Size</div>
            <div style={{ textAlign: "right" }}>{prettySize(file.size)}</div>
            <div>Type</div>
            <div style={{ textAlign: "right" }}>{file.type || "model/stl"}</div>
          </div>
        )}
      </div>

      <div className="controls" style={{ marginTop: 10 }}>
        <button
          className="btn secondary"
          onClick={() => onFileSelected(null)}
          disabled={!file}
          type="button"
        >
          Remove
        </button>
        <div style={{ flex: 1 }} />
        <button
          className="btn"
          onClick={onStartPreview}
          disabled={!file || disabled}
          type="button"
        >
          Preview
        </button>
        <button
          className="btn primary"
          onClick={onStartJob}
          disabled={!file || disabled}
          type="button"
        >
          Process
        </button>
      </div>

      <p style={{ marginTop: 8, fontSize: 12, color: "var(--muted)" }}>
        Tip: Models work best when manifold and roughly millimeter scale. Max
        upload defaults to 100&nbsp;MB.
      </p>
    </div>
  );
}
