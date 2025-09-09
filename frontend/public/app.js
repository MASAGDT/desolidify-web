var __getOwnPropNames = Object.getOwnPropertyNames;
var __esm = (fn, res) => function __init() {
  return fn && (res = (0, fn[__getOwnPropNames(fn)[0]])(fn = 0)), res;
};
var __commonJS = (cb, mod) => function __require() {
  return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
};

// src/api.js
async function jsonFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      ...options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
      ...options.headers || {}
    },
    ...options
  });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      if (data && data.error) msg = data.error;
    } catch {
    }
    throw new Error(msg);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    return res.json();
  }
  return res.arrayBuffer();
}
async function getParamSpec() {
  return jsonFetch("/meta/params");
}
async function getPresets() {
  return jsonFetch("/meta/presets");
}
async function createJob(file, params = {}, presetName) {
  const fd = new FormData();
  fd.append("file", file, file?.name || "model.stl");
  if (params && typeof params === "object") {
    fd.append("params", JSON.stringify(params));
  }
  if (presetName) fd.append("preset", String(presetName));
  return jsonFetch("/jobs", { method: "POST", body: fd });
}
async function getJobStatus(jobId) {
  return jsonFetch(`/jobs/${encodeURIComponent(jobId)}`, { method: "GET" });
}
async function fetchJobResultBlob(jobId) {
  const res = await fetch(
    `${API_BASE}/jobs/${encodeURIComponent(jobId)}/result`,
    { method: "GET" }
  );
  if (res.status === 202) {
    const data = await res.json();
    const msg = data?.error || data?.message || "Result not ready";
    throw new Error(msg);
  }
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.blob();
}
async function runPreview(file, params = {}) {
  const fd = new FormData();
  fd.append("file", file, file?.name || "model.stl");
  fd.append("params", JSON.stringify({ ...params, fast: 2 }));
  const res = await fetch(`${API_BASE}/preview`, { method: "POST", body: fd });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      msg = j?.error || msg;
    } catch {
    }
    throw new Error(msg);
  }
  return res.blob();
}
var RUNTIME, API_BASE;
var init_api = __esm({
  "src/api.js"() {
    RUNTIME = typeof window !== "undefined" && window.__DESOLIDIFY__ || {};
    API_BASE = RUNTIME.apiBase || "/api";
  }
});

// src/components/UploadPanel.jsx
import React, { useCallback, useRef, useState } from "react";
function UploadPanel({
  file,
  onFileSelected,
  onStartPreview,
  onStartJob,
  disabled
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
    if (!Number.isFinite(n)) return "\u2014";
    const u = ["B", "KB", "MB", "GB"];
    let i = 0;
    while (n >= 1024 && i < u.length - 1) {
      n /= 1024;
      i++;
    }
    return `${n.toFixed(1)} ${u[i]}`;
  }
  return /* @__PURE__ */ React.createElement("div", { className: "card" }, /* @__PURE__ */ React.createElement("h3", { className: "card-title" }, "Upload STL"), /* @__PURE__ */ React.createElement(
    "div",
    {
      className: "uploader",
      onDragEnter: onDrag,
      onDragOver: onDrag,
      onDragLeave: onDrag,
      onDrop,
      style: {
        border: "1px dashed var(--border)",
        borderRadius: 12,
        padding: 16,
        background: dragOver ? "#191c2b" : "#141726",
        cursor: "pointer"
      },
      onClick: openPicker
    },
    /* @__PURE__ */ React.createElement(
      "input",
      {
        ref: inputRef,
        type: "file",
        accept: ".stl,model/stl",
        onChange,
        hidden: true
      }
    ),
    !file ? /* @__PURE__ */ React.createElement("div", { style: { textAlign: "center", color: "var(--muted)" } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 13, marginBottom: 6 } }, "Drag & drop an ", /* @__PURE__ */ React.createElement("strong", null, ".stl"), " file here"), /* @__PURE__ */ React.createElement("div", { style: { fontSize: 12 } }, "or click to browse")) : /* @__PURE__ */ React.createElement("div", { className: "kv" }, /* @__PURE__ */ React.createElement("div", null, "File"), /* @__PURE__ */ React.createElement("div", { style: { textAlign: "right" } }, file.name), /* @__PURE__ */ React.createElement("div", null, "Size"), /* @__PURE__ */ React.createElement("div", { style: { textAlign: "right" } }, prettySize(file.size)), /* @__PURE__ */ React.createElement("div", null, "Type"), /* @__PURE__ */ React.createElement("div", { style: { textAlign: "right" } }, file.type || "model/stl"))
  ), /* @__PURE__ */ React.createElement("div", { className: "controls", style: { marginTop: 10 } }, /* @__PURE__ */ React.createElement(
    "button",
    {
      className: "btn secondary",
      onClick: () => onFileSelected(null),
      disabled: !file,
      type: "button"
    },
    "Remove"
  ), /* @__PURE__ */ React.createElement("div", { style: { flex: 1 } }), /* @__PURE__ */ React.createElement(
    "button",
    {
      className: "btn",
      onClick: onStartPreview,
      disabled: !file || disabled,
      type: "button"
    },
    "Preview"
  ), /* @__PURE__ */ React.createElement(
    "button",
    {
      className: "btn primary",
      onClick: onStartJob,
      disabled: !file || disabled,
      type: "button"
    },
    "Process"
  )), /* @__PURE__ */ React.createElement("p", { style: { marginTop: 8, fontSize: 12, color: "var(--muted)" } }, "Tip: Models work best when manifold and roughly millimeter scale. Max upload defaults to 100\xA0MB."));
}
var init_UploadPanel = __esm({
  "src/components/UploadPanel.jsx"() {
  }
});

// src/components/PresetSelect.jsx
import React2 from "react";
function PresetSelect({ presets = {}, value, onChange }) {
  const names = Object.keys(presets || {});
  return /* @__PURE__ */ React2.createElement("div", { className: "row" }, /* @__PURE__ */ React2.createElement(
    "select",
    {
      className: "input",
      value: value || "",
      onChange: (e) => onChange?.(e.target.value)
    },
    !value && /* @__PURE__ */ React2.createElement("option", { value: "" }, "\u2014 Select a preset \u2014"),
    names.map((n) => /* @__PURE__ */ React2.createElement("option", { key: n, value: n }, n))
  ));
}
var init_PresetSelect = __esm({
  "src/components/PresetSelect.jsx"() {
  }
});

// src/components/Tooltip.jsx
import React3 from "react";
function Tooltip({ text }) {
  if (!text) return null;
  return /* @__PURE__ */ React3.createElement(
    "span",
    {
      title: text,
      "aria-label": text,
      style: {
        display: "inline-block",
        marginLeft: 6,
        color: "var(--muted)",
        background: "#2a2e45",
        borderRadius: 6,
        padding: "0 6px",
        fontSize: 10,
        lineHeight: "16px",
        verticalAlign: "middle"
      }
    },
    "?"
  );
}
var init_Tooltip = __esm({
  "src/components/Tooltip.jsx"() {
  }
});

// src/components/ParamSliders.jsx
import React4, { useMemo, useState as useState2 } from "react";
function NumRow({ k, spec, value, onChange }) {
  const step = spec.step ?? (spec.type === "integer" ? 1 : 0.1);
  const min = spec.min ?? 0;
  const max = spec.max ?? 100;
  const v = value ?? spec.default ?? min;
  return /* @__PURE__ */ React4.createElement("div", { style: { marginBottom: 10 } }, /* @__PURE__ */ React4.createElement("div", { className: "row", style: { justifyContent: "space-between" } }, /* @__PURE__ */ React4.createElement("label", { htmlFor: `param-${k}`, style: { fontSize: 12 } }, k, " ", /* @__PURE__ */ React4.createElement(Tooltip, { text: spec.tip })), /* @__PURE__ */ React4.createElement(
    "input",
    {
      className: "input",
      style: { width: 110, textAlign: "right" },
      id: `param-${k}-num`,
      type: "number",
      step,
      min,
      max,
      value: v ?? "",
      onChange: (e) => onChange({ [k]: e.target.value === "" ? null : Number(e.target.value) })
    }
  )), /* @__PURE__ */ React4.createElement(
    "input",
    {
      id: `param-${k}`,
      type: "range",
      min,
      max,
      step,
      value: Number.isFinite(v) ? v : min,
      onChange: (e) => onChange({ [k]: Number(e.target.value) }),
      style: { width: "100%" }
    }
  ));
}
function BoolRow({ k, spec, value, onChange }) {
  const v = !!(value ?? spec.default);
  return /* @__PURE__ */ React4.createElement("div", { className: "row", style: { marginBottom: 10 } }, /* @__PURE__ */ React4.createElement("label", { htmlFor: `param-${k}`, style: { fontSize: 12 } }, k, " ", /* @__PURE__ */ React4.createElement(Tooltip, { text: spec.tip })), /* @__PURE__ */ React4.createElement("div", { style: { flex: 1 } }), /* @__PURE__ */ React4.createElement(
    "input",
    {
      id: `param-${k}`,
      type: "checkbox",
      checked: v,
      onChange: (e) => onChange({ [k]: !!e.target.checked })
    }
  ));
}
function SelectRow({ k, spec, value, onChange }) {
  const v = (value ?? spec.default) || "";
  return /* @__PURE__ */ React4.createElement("div", { className: "row", style: { marginBottom: 10 } }, /* @__PURE__ */ React4.createElement("label", { htmlFor: `param-${k}`, style: { fontSize: 12 } }, k, " ", /* @__PURE__ */ React4.createElement(Tooltip, { text: spec.tip })), /* @__PURE__ */ React4.createElement("div", { style: { flex: 1 } }), /* @__PURE__ */ React4.createElement(
    "select",
    {
      id: `param-${k}`,
      className: "input",
      style: { width: 180 },
      value: v,
      onChange: (e) => onChange({ [k]: e.target.value })
    },
    (spec.choices || []).map((c) => /* @__PURE__ */ React4.createElement("option", { key: c, value: c }, c))
  ));
}
function ParamSliders({ specs = {}, values = {}, onChange }) {
  const [showAdvanced, setShowAdvanced] = useState2(false);
  const entries = useMemo(() => Object.entries(specs), [specs]);
  const mainKeys = useMemo(
    () => entries.map(([k]) => k).filter((k) => !["chunk", "mem_delay", "mem_tries"].includes(k)),
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
    if (type === "bool") return /* @__PURE__ */ React4.createElement(BoolRow, { key: k, k, spec, value: v, onChange });
    if (type === "select") return /* @__PURE__ */ React4.createElement(SelectRow, { key: k, k, spec, value: v, onChange });
    return /* @__PURE__ */ React4.createElement(NumRow, { key: k, k, spec, value: v, onChange });
  };
  return /* @__PURE__ */ React4.createElement("div", null, mainKeys.map(renderRow), advancedKeys.length > 0 && /* @__PURE__ */ React4.createElement(React4.Fragment, null, /* @__PURE__ */ React4.createElement("div", { className: "row", style: { marginTop: 6, marginBottom: 6 } }, /* @__PURE__ */ React4.createElement("div", { style: { fontSize: 12, color: "var(--muted)" } }, "Advanced"), /* @__PURE__ */ React4.createElement("div", { style: { flex: 1 } }), /* @__PURE__ */ React4.createElement(
    "button",
    {
      className: "btn ghost",
      type: "button",
      onClick: () => setShowAdvanced((s) => !s)
    },
    showAdvanced ? "Hide" : "Show"
  )), showAdvanced && advancedKeys.map(renderRow)));
}
var init_ParamSliders = __esm({
  "src/components/ParamSliders.jsx"() {
    init_Tooltip();
  }
});

// src/components/Preview3D.jsx
import React5, { useEffect, useRef as useRef2, useState as useState3 } from "react";
function Preview3D({ beforeUrl = null, afterUrl = null }) {
  const mountRef = useRef2(null);
  const stateRef = useRef2({
    renderer: null,
    scene: null,
    camera: null,
    mesh: null,
    anim: 0,
    width: 0,
    height: 0,
    three: null,
    STLLoader: null,
    root: null
  });
  const [ready, setReady] = useState3(false);
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const three = await import("/vendor/three/three.module.js");
        const STL = await import("/vendor/three/STLLoader.js");
        if (!mounted) return;
        stateRef.current.three = three;
        stateRef.current.STLLoader = STL.STLLoader || STL.default?.STLLoader || STL.default || STL;
        setReady(true);
      } catch (e) {
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);
  useEffect(() => {
    if (!ready || !mountRef.current) return;
    const S = stateRef.current;
    if (S.renderer) return;
    const THREE = S.three;
    const el = mountRef.current;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
    renderer.setClearColor(0, 0);
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.01, 1e4);
    camera.position.set(100, 120, 160);
    const root = new THREE.Group();
    scene.add(root);
    const amb = new THREE.AmbientLight(16777215, 0.6);
    scene.add(amb);
    const dir = new THREE.DirectionalLight(16777215, 0.8);
    dir.position.set(1, 1.2, 0.7).multiplyScalar(200);
    scene.add(dir);
    S.renderer = renderer;
    S.scene = scene;
    S.camera = camera;
    S.root = root;
    const resize = () => {
      const rect = el.getBoundingClientRect();
      const w = Math.max(10, rect.width | 0);
      const h = Math.max(10, rect.height | 0);
      if (w === S.width && h === S.height) return;
      S.width = w;
      S.height = h;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    resize();
    S._onResize = resize;
    window.addEventListener("resize", resize);
    const animate = () => {
      S.anim = requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();
    let dragging = false;
    let lx = 0, ly = 0;
    const onDown = (e) => {
      dragging = true;
      lx = e.clientX;
      ly = e.clientY;
    };
    const onUp = () => {
      dragging = false;
    };
    const onMove = (e) => {
      if (!dragging || !S.root) return;
      const dx = (e.clientX - lx) * 5e-3;
      const dy = (e.clientY - ly) * 5e-3;
      S.root.rotation.y += dx;
      S.root.rotation.x += dy;
      lx = e.clientX;
      ly = e.clientY;
    };
    el.addEventListener("mousedown", onDown);
    window.addEventListener("mouseup", onUp);
    window.addEventListener("mousemove", onMove);
    return () => {
      window.removeEventListener("resize", resize);
      el.removeEventListener("mousedown", onDown);
      window.removeEventListener("mouseup", onUp);
      window.removeEventListener("mousemove", onMove);
      if (S.anim) cancelAnimationFrame(S.anim);
      if (S.renderer) {
        try {
          S.renderer.dispose();
        } catch {
        }
        try {
          el.removeChild(S.renderer.domElement);
        } catch {
        }
      }
      S.renderer = null;
      S.scene = null;
      S.camera = null;
      S.root = null;
    };
  }, [ready]);
  useEffect(() => {
    const url = afterUrl || beforeUrl;
    const S = stateRef.current;
    if (!ready || !url || !S.three || !S.STLLoader || !S.root) {
      if (S.mesh && S.root) {
        S.root.remove(S.mesh);
        S.mesh.geometry?.dispose?.();
        S.mesh.material?.dispose?.();
        S.mesh = null;
      }
      return;
    }
    let canceled = false;
    const THREE = S.three;
    const loader = new S.STLLoader();
    loader.load(
      url,
      (geom) => {
        if (canceled) return;
        if (S.mesh && S.root) {
          S.root.remove(S.mesh);
          S.mesh.geometry?.dispose?.();
          S.mesh.material?.dispose?.();
          S.mesh = null;
        }
        const geometry = geom.isBufferGeometry ? geom : new THREE.BufferGeometry().fromGeometry(geom);
        geometry.computeVertexNormals();
        const mat = new THREE.MeshStandardMaterial({
          color: afterUrl ? 6989823 : 11184810,
          roughness: 0.6,
          metalness: 0.05
        });
        const mesh = new THREE.Mesh(geometry, mat);
        S.root.add(mesh);
        S.mesh = mesh;
        geometry.computeBoundingBox();
        const bb = geometry.boundingBox;
        const size = new THREE.Vector3();
        bb.getSize(size);
        const center = new THREE.Vector3();
        bb.getCenter(center);
        mesh.position.sub(center);
        const maxDim = Math.max(size.x, size.y, size.z) || 1;
        const dist = maxDim * 2.2;
        S.camera.position.set(dist, dist * 0.9, dist * 1.2);
        S.camera.near = Math.max(0.01, dist / 100);
        S.camera.far = dist * 10;
        S.camera.lookAt(0, 0, 0);
        S.camera.updateProjectionMatrix();
      },
      void 0,
      () => {
      }
    );
    return () => {
      canceled = true;
    };
  }, [beforeUrl, afterUrl, ready]);
  return /* @__PURE__ */ React5.createElement(
    "div",
    {
      ref: mountRef,
      style: {
        width: "100%",
        height: 300,
        background: "linear-gradient(180deg, rgba(17,18,24,0.8), rgba(12,14,20,0.8))"
      }
    },
    !ready && /* @__PURE__ */ React5.createElement("div", { style: { padding: 12, color: "var(--muted)", fontSize: 12 } }, "Viewer initializing\u2026")
  );
}
var init_Preview3D = __esm({
  "src/components/Preview3D.jsx"() {
  }
});

// src/components/ProgressBar.jsx
import React6 from "react";
function ProgressBar({ value = 0 }) {
  const pct = Math.max(0, Math.min(1, Number.isFinite(value) ? value : 0));
  return /* @__PURE__ */ React6.createElement(
    "div",
    {
      style: {
        width: "100%",
        height: 10,
        borderRadius: 999,
        background: "#1b1e2c",
        border: "1px solid var(--border)",
        overflow: "hidden"
      },
      "aria-valuemin": 0,
      "aria-valuemax": 100,
      "aria-valuenow": Math.round(pct * 100),
      role: "progressbar"
    },
    /* @__PURE__ */ React6.createElement(
      "div",
      {
        style: {
          width: `${pct * 100}%`,
          height: "100%",
          background: "linear-gradient(90deg, rgba(42,114,255,1), rgba(94,210,255,1))",
          transition: "width 260ms ease"
        }
      }
    )
  );
}
var init_ProgressBar = __esm({
  "src/components/ProgressBar.jsx"() {
  }
});

// src/App.jsx
import React7, { useEffect as useEffect2, useMemo as useMemo2, useRef as useRef3, useState as useState4 } from "react";
function App() {
  const [specs, setSpecs] = useState4({});
  const [presets, setPresets] = useState4({});
  const [selectedPreset, setSelectedPreset] = useState4(null);
  const [params, setParams] = useState4({});
  const [file, setFile] = useState4(null);
  const [jobId, setJobId] = useState4(null);
  const [progress, setProgress] = useState4(0);
  const [statusMsg, setStatusMsg] = useState4("");
  const [state, setState] = useState4("idle");
  const [previewUrl, setPreviewUrl] = useState4(null);
  const [resultUrl, setResultUrl] = useState4(null);
  const inputUrlRef = useRef3(null);
  useEffect2(() => {
    let mounted = true;
    (async () => {
      try {
        const [s, p] = await Promise.all([getParamSpec(), getPresets()]);
        if (!mounted) return;
        setSpecs(s || {});
        setPresets(p || {});
        const presetNames = Object.keys(p || {});
        if (presetNames.length && !selectedPreset) {
          setSelectedPreset(presetNames[0]);
          const defaults = Object.fromEntries(
            Object.entries(s || {}).map(([k, v]) => [k, v.default])
          );
          setParams({ ...defaults, ...p[presetNames[0]] || {} });
        } else if (!selectedPreset) {
          const defaults = Object.fromEntries(
            Object.entries(s || {}).map(([k, v]) => [k, v.default])
          );
          setParams(defaults);
        }
      } catch {
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);
  useEffect2(() => {
    if (inputUrlRef.current) {
      URL.revokeObjectURL(inputUrlRef.current);
      inputUrlRef.current = null;
    }
    if (file) {
      inputUrlRef.current = URL.createObjectURL(file);
    }
    return () => {
      if (inputUrlRef.current) {
        URL.revokeObjectURL(inputUrlRef.current);
        inputUrlRef.current = null;
      }
    };
  }, [file]);
  useEffect2(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      if (resultUrl) URL.revokeObjectURL(resultUrl);
    };
  }, [previewUrl, resultUrl]);
  const canStart = useMemo2(() => !!file && state !== "running", [file, state]);
  async function handleStartPreview() {
    if (!file) return;
    try {
      setState("running");
      setStatusMsg("Generating preview\u2026");
      setProgress(0.02);
      const blob = await runPreview(file, { ...params, fast: 2 });
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
      setProgress(0.3);
      setStatusMsg("Preview ready.");
      setState("idle");
    } catch (e) {
      setState("error");
      setStatusMsg(String(e?.message || e || "Preview failed"));
    }
  }
  async function handleStartJob() {
    if (!file) return;
    try {
      setState("queued");
      setProgress(0);
      setStatusMsg("Uploading\u2026");
      const resp = await createJob(file, params, selectedPreset || void 0);
      const id = resp?.job_id;
      setJobId(id);
      setStatusMsg("Queued.");
      pollUntilDone(id);
    } catch (e) {
      setState("error");
      setStatusMsg(String(e?.message || e || "Job failed to start"));
    }
  }
  function pollUntilDone(id) {
    let timer = null;
    const tick = async () => {
      try {
        const st = await getJobStatus(id);
        if (!st) return;
        setState(st.state || "unknown");
        setProgress(typeof st.progress === "number" ? st.progress : 0);
        setStatusMsg(st.message || st.state);
        if (st.state === "finished") {
          clearInterval(timer);
          setProgress(1);
          setStatusMsg("Fetching result\u2026");
          const blob = await fetchJobResultBlob(id);
          if (resultUrl) URL.revokeObjectURL(resultUrl);
          const url = URL.createObjectURL(blob);
          setResultUrl(url);
          setStatusMsg("Complete.");
          setState("finished");
        } else if (st.state === "error") {
          clearInterval(timer);
          setState("error");
        }
      } catch (e) {
      }
    };
    timer = setInterval(tick, POLL_MS);
    tick();
  }
  function handlePresetChange(name) {
    setSelectedPreset(name);
    const defaults = Object.fromEntries(
      Object.entries(specs || {}).map(([k, v]) => [k, v.default])
    );
    setParams({ ...defaults, ...presets[name] || {} });
  }
  function handleParamChange(next) {
    setParams((prev) => ({ ...prev, ...next }));
  }
  function handleNewFile(f) {
    setFile(f || null);
    setPreviewUrl((old) => {
      if (old) URL.revokeObjectURL(old);
      return null;
    });
    setResultUrl((old) => {
      if (old) URL.revokeObjectURL(old);
      return null;
    });
    setState("idle");
    setProgress(0);
    setStatusMsg("");
  }
  return /* @__PURE__ */ React7.createElement("div", { className: "app-root" }, /* @__PURE__ */ React7.createElement("header", { className: "app-header" }, /* @__PURE__ */ React7.createElement("h1", null, "desolidify-web"), /* @__PURE__ */ React7.createElement("div", { className: "header-actions" }, /* @__PURE__ */ React7.createElement("a", { href: "/", className: "link-muted" }, "Reset"))), /* @__PURE__ */ React7.createElement("main", { className: "app-main" }, /* @__PURE__ */ React7.createElement("section", { className: "left-panel" }, /* @__PURE__ */ React7.createElement(
    UploadPanel,
    {
      file,
      onFileSelected: handleNewFile,
      onStartPreview: handleStartPreview,
      onStartJob: handleStartJob,
      disabled: !file
    }
  ), /* @__PURE__ */ React7.createElement("div", { className: "card" }, /* @__PURE__ */ React7.createElement("h3", { className: "card-title" }, "Preset"), /* @__PURE__ */ React7.createElement(
    PresetSelect,
    {
      presets,
      value: selectedPreset,
      onChange: handlePresetChange
    }
  )), /* @__PURE__ */ React7.createElement("div", { className: "card" }, /* @__PURE__ */ React7.createElement("h3", { className: "card-title" }, "Parameters"), /* @__PURE__ */ React7.createElement(
    ParamSliders,
    {
      specs,
      values: params,
      onChange: handleParamChange
    }
  )), /* @__PURE__ */ React7.createElement("div", { className: "card" }, /* @__PURE__ */ React7.createElement("h3", { className: "card-title" }, "Progress"), /* @__PURE__ */ React7.createElement(ProgressBar, { value: progress }), /* @__PURE__ */ React7.createElement("div", { className: `status ${state}` }, statusMsg || "\u2014"))), /* @__PURE__ */ React7.createElement("section", { className: "right-panel" }, /* @__PURE__ */ React7.createElement("div", { className: "viewer-grid" }, /* @__PURE__ */ React7.createElement("div", { className: "viewer-card" }, /* @__PURE__ */ React7.createElement("div", { className: "viewer-title" }, "Input"), /* @__PURE__ */ React7.createElement(Preview3D, { beforeUrl: inputUrlRef.current, afterUrl: null })), /* @__PURE__ */ React7.createElement("div", { className: "viewer-card" }, /* @__PURE__ */ React7.createElement("div", { className: "viewer-title" }, "Preview"), /* @__PURE__ */ React7.createElement(Preview3D, { beforeUrl: null, afterUrl: previewUrl })), /* @__PURE__ */ React7.createElement("div", { className: "viewer-card" }, /* @__PURE__ */ React7.createElement("div", { className: "viewer-title" }, "Result"), /* @__PURE__ */ React7.createElement(Preview3D, { beforeUrl: null, afterUrl: resultUrl }))))), /* @__PURE__ */ React7.createElement("footer", { className: "app-footer" }, /* @__PURE__ */ React7.createElement("span", null, "\xA9 ", (/* @__PURE__ */ new Date()).getFullYear(), " desolidify-web"), /* @__PURE__ */ React7.createElement("span", { className: "dot" }, "\u2022"), /* @__PURE__ */ React7.createElement("span", null, "Local runtime")));
}
var POLL_MS;
var init_App = __esm({
  "src/App.jsx"() {
    init_api();
    init_UploadPanel();
    init_PresetSelect();
    init_ParamSliders();
    init_Preview3D();
    init_ProgressBar();
    POLL_MS = 1200;
  }
});

// src/index.jsx
import React8 from "react";
import ReactDOM from "react-dom/client";
var require_index = __commonJS({
  "src/index.jsx"() {
    init_App();
    var root = ReactDOM.createRoot(document.getElementById("root"));
    root.render(
      /* @__PURE__ */ React8.createElement(React8.StrictMode, null, /* @__PURE__ */ React8.createElement(App, null))
    );
  }
});
export default require_index();
//# sourceMappingURL=app.js.map
