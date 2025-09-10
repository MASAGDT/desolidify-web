// frontend/src/App.jsx
import React, { useEffect, useRef, useState } from "react";
import {
  getParamSpec,
  getPresets,
  createJob,
  getJobStatus,
  fetchJobResultBlob,
  runPreview,
  cancelAllJobs,
} from "./api";

// Components
import UploadPanel from "./components/UploadPanel.jsx";
import PresetSelect from "./components/PresetSelect.jsx";
import ParamSliders from "./components/ParamSliders.jsx";
import Preview3D from "./components/Preview3D.jsx";
import ProgressBar from "./components/ProgressBar.jsx";

const POLL_MS = 1200;

export default function App() {
  const [specs, setSpecs] = useState({});
  const [presets, setPresets] = useState({});
  const [selectedPreset, setSelectedPreset] = useState(null);
  const [params, setParams] = useState({});
  const [file, setFile] = useState(null);

  const [jobId, setJobId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState("");
  const [state, setState] = useState("idle"); // idle|queued|running|finished|error

  const [previewUrl, setPreviewUrl] = useState(null);
  const [resultUrl, setResultUrl] = useState(null);
  const inputUrlRef = useRef(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load meta specs + presets
  useEffect(() => {
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
          setParams({ ...defaults, ...(p[presetNames[0]] || {}) });
        } else if (!selectedPreset) {
          const defaults = Object.fromEntries(
            Object.entries(s || {}).map(([k, v]) => [k, v.default])
          );
          setParams(defaults);
        }
      } catch {
        // ignore errors during initial load
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  // Maintain object URL for input STL
  useEffect(() => {
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

  // Cleanup preview/result URLs on unmount
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      if (resultUrl) URL.revokeObjectURL(resultUrl);
    };
  }, [previewUrl, resultUrl]);

  async function handleStartPreview() {
    if (!file || isSubmitting) return;
    setIsSubmitting(true);
    try {
      setState("running");
      setStatusMsg("Generating preview…");
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
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleStartJob() {
    if (!file || isSubmitting) return;
    setIsSubmitting(true);
    try {
      setState("queued");
      setProgress(0.0);
      setStatusMsg("Uploading…");
      const resp = await createJob(file, params, selectedPreset || undefined);
      const id = resp?.job_id;
      setJobId(id);
      setStatusMsg("Queued.");
      pollUntilDone(id);
    } catch (e) {
      setState("error");
      setStatusMsg(String(e?.message || e || "Job failed to start"));
    } finally {
      setIsSubmitting(false);
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
          setProgress(1.0);
          setStatusMsg("Fetching result…");
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
      } catch {
        // keep polling even on transient errors
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
    setParams({ ...defaults, ...(presets[name] || {}) });
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

  async function handleCancelJobs() {
    try {
      await cancelAllJobs();
      setJobId(null);
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
      setStatusMsg("Cancelled.");
    } catch (e) {
      setStatusMsg(String(e?.message || "Cancel failed"));
    }
  }

  return (
    <div className="app-root">
      <header className="app-header">
        <h1>desolidify-web</h1>
        <div className="header-actions">
          <a href="/" className="link-muted">Reset</a>
          <button onClick={handleCancelJobs} className="link-muted" type="button">
            Cancel Jobs
          </button>
        </div>
      </header>

      <main className="app-main">
        <section className="left-panel">
          <UploadPanel
            file={file}
            onFileSelected={handleNewFile}
            onStartPreview={handleStartPreview}
            onStartJob={handleStartJob}
            disabled={!file || isSubmitting || state === "queued" || state === "running"}
          />

          <div className="card">
            <h3 className="card-title">Preset</h3>
            <PresetSelect
              presets={presets}
              value={selectedPreset}
              onChange={handlePresetChange}
            />
          </div>

          <div className="card">
            <h3 className="card-title">Parameters</h3>
            <ParamSliders
              specs={specs}
              values={params}
              onChange={handleParamChange}
            />
          </div>

          <div className="card">
            <h3 className="card-title">Progress</h3>
            <ProgressBar value={progress} />
            <div className={`status ${state}`}>{statusMsg || "—"}</div>
          </div>
        </section>

        <section className="right-panel">
          <div className="viewer-grid">
            <div className="viewer-card">
              <div className="viewer-title">Input</div>
              <Preview3D beforeUrl={inputUrlRef.current} afterUrl={null} />
            </div>
            <div className="viewer-card">
              <div className="viewer-title">Preview</div>
              <Preview3D beforeUrl={null} afterUrl={previewUrl} />
            </div>
            <div className="viewer-card">
              <div className="viewer-title">Result</div>
              <Preview3D beforeUrl={null} afterUrl={resultUrl} />
            </div>
          </div>
        </section>
      </main>

      <footer className="app-footer">
        <span>© {new Date().getFullYear()} desolidify-web</span>
        <span className="dot">•</span>
        <span>Local runtime</span>
      </footer>
    </div>
  );
}
