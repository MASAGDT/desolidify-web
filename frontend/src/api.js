// frontend/src/api.js
const RUNTIME = (typeof window !== "undefined" && window.__DESOLIDIFY__) || {};
const API_BASE = RUNTIME.apiBase || "/api";

async function jsonFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      ...(options.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...(options.headers || {}),
    },
    ...options,
  });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      if (data && data.error) msg = data.error;
    } catch {}
    throw new Error(msg);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    return res.json();
  }
  return res.arrayBuffer();
}

export async function getParamSpec() {
  return jsonFetch("/meta/params");
}

export async function getPresets() {
  return jsonFetch("/meta/presets");
}

export async function createJob(file, params = {}, presetName) {
  const fd = new FormData();
  fd.append("file", file, file?.name || "model.stl");
  if (params && typeof params === "object") {
    fd.append("params", JSON.stringify(params));
  }
  if (presetName) fd.append("preset", String(presetName));
  return jsonFetch("/jobs", { method: "POST", body: fd });
}

export async function getJobStatus(jobId) {
  return jsonFetch(`/jobs/${encodeURIComponent(jobId)}`, { method: "GET" });
}

export async function fetchJobResultBlob(jobId) {
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

export async function cancelAllJobs() {
  return jsonFetch("/jobs", { method: "DELETE" });
}

// TODO: optional: Socket.IO hookup when server join-room handler is available.
// import { io } from "socket.io-client";
// export function connectProgress(jobId, onProgress) {
//   const url = RUNTIME.wsNamespace || "/";
//   const socket = io(url, { transports: ["websocket", "polling"] });
//   socket.on("connect", () => {
//     socket.emit("join", { room: `job:${jobId}` });
//   });
//   socket.on("progress", (payload) => {
//     if (payload?.job_id === jobId && typeof onProgress === "function") {
//       onProgress(payload);
//     }
//   });
//   return () => {
//     try {
//       socket.emit("leave", { room: `job:${jobId}` });
//       socket.disconnect();
//     } catch {}
//   };
// }
