import React, { useState, useRef, useEffect } from "react";
import ModelViewer from "./ModelViewer";
import "./App.css";

// ─── Backend API base ──────────────────────────────────────────────────────
// Frontend runs on :5173 (Vite), backend runs on :8000 (FastAPI) -- different
// origins, so every API call needs the full URL, not a relative path.
const API_BASE = "http://localhost:8000";

// ─── Default/placeholder detection data (shown before any upload) ─────────
const DEFAULT_DETECTIONS = {
  walls:    { count: 14, color: "var(--wall-color)" },
  doors:    { count: 8,  color: "var(--door-color)" },
  windows:  { count: 5,  color: "var(--window-color)" },
  rooms:    { count: 4,  color: "var(--room-color)" },
  furniture:{ count: 0,  color: "var(--furniture-color)" },
};

// ─── 3D view controls config ──────────────────────────────────────────────
const CONTROLS = [
  { id: "rotate",    icon: "↺",  label: "Rotate" },
  { id: "pan",       icon: "✥",  label: "Pan" },
  { id: "zoom",      icon: "⊕",  label: "Zoom" },
  { id: "top",       icon: "⬛", label: "Top View" },
  { id: "wireframe", icon: "⬡",  label: "Wireframe" },
  { id: "realistic", icon: "◑",  label: "Realistic" },
];

// ─── AI Detection Overlay (SVG drawing of walls / rooms / doors / windows) ─
// NOTE: this still draws hardcoded coordinates from the original test.png.
// It is NOT yet wired to the real uploaded image's detections -- doing that
// properly means redrawing from the live detections.json bboxes, scaled to
// whatever image the user actually uploaded (different plans = different
// pixel dimensions). Left as-is for now since it's cosmetic, not blocking;
// flagged here so it isn't mistaken for already being dynamic.
function DetectionOverlay() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width;
    const H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    const srcW = 2000;
    const srcH = 1540;
    const srcX0 = 0;
    const srcY0 = 660;
    const sx = W / srcW;
    const sy = H / srcH;

    function px(x, y) {
      return [(x - srcX0) * sx, (y - srcY0) * sy];
    }

    const walls = [
      [[279, 2168], [1739, 2168]],
      [[276, 680],  [1773, 680]],
      [[1274, 1184],[1787, 1184]],
      [[1279, 1672],[1790, 1672]],
      [[1267, 984], [1782, 984]],
      [[1051, 1592],[1289, 1592]],
      [[765, 1952], [1287, 1952]],
      [[1280, 1472],[1780, 1472]],
      [[1768, 662], [1768, 2110]],
      [[792, 1943], [792, 2185]],
      [[1064, 1580],[1064, 1692]],
      [[1288, 1170],[1288, 1895]],
      [[304, 657],  [304, 2104]],
    ];

    ctx.strokeStyle = "#8892a4";
    ctx.lineWidth = 2;
    walls.forEach(([a, b]) => {
      const [ax, ay] = px(...a);
      const [bx, by] = px(...b);
      ctx.beginPath();
      ctx.moveTo(ax, ay);
      ctx.lineTo(bx, by);
      ctx.stroke();
    });

    const rooms = [
      [[304, 660], [1768, 660], [1768, 2110], [304, 2110]],
      [[304, 660], [1288, 660], [1288, 1170], [304, 1170]],
      [[304, 1592],[1064, 1592],[1064, 1952], [304, 1952]],
      [[1064, 1592],[1288, 1592],[1288, 1952],[1064, 1952]],
    ];

    rooms.forEach((pts, i) => {
      const colors = ["#68d391","#4fd1c5","#68d391","#b794f4"];
      ctx.strokeStyle = colors[i % colors.length];
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      const [x0, y0] = px(...pts[0]);
      ctx.moveTo(x0, y0);
      pts.slice(1).forEach(p => {
        const [xi, yi] = px(...p);
        ctx.lineTo(xi, yi);
      });
      ctx.closePath();
      ctx.stroke();
      ctx.setLineDash([]);
    });

    const doors = [
      [1082, 521, 1214, 700],
      [1328, 534, 1472, 704],
      [1270, 1710, 1417, 1844],
      [1147, 772, 1281, 900],
      [891, 2162, 1013, 2317],
      [1750, 1496, 1928, 1633],
      [1144, 1831, 1274, 1939],
      [1430, 872, 1534, 977],
    ];

    ctx.strokeStyle = "#f6ad55";
    ctx.lineWidth = 1.5;
    doors.forEach(([x1, y1, x2, y2]) => {
      const [ax, ay] = px(x1, y1);
      const [bx, by] = px(x2, y2);
      ctx.strokeRect(ax, ay, bx - ax, by - ay);
    });

    const windows = [
      [542, 659, 729, 700],
      [732, 659, 926, 700],
      [288, 1332, 320, 1511],
      [1747, 833, 1791, 963],
      [1759, 1702, 1797, 1922],
    ];

    ctx.strokeStyle = "#63b3ed";
    ctx.lineWidth = 1.5;
    windows.forEach(([x1, y1, x2, y2]) => {
      const [ax, ay] = px(x1, y1);
      const [bx, by] = px(x2, y2);
      ctx.strokeRect(ax, ay, bx - ax, by - ay);
    });

    const labels = [
      { text: "BEDROOM 3", x: 680, y: 1800 },
      { text: "BEDROOM 2", x: 680, y: 870 },
      { text: "BATHROOM", x: 750, y: 1720 },
      { text: "LIVING", x: 1100, y: 1300 },
    ];

    ctx.fillStyle = "#fc8181";
    ctx.font = "bold 8px Inter, sans-serif";
    ctx.textAlign = "center";
    labels.forEach(({ text, x, y }) => {
      const [cx, cy] = px(x, y);
      ctx.fillText(text, cx, cy);
    });

  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="overlay-canvas"
      width={200}
      height={190}
      style={{ width: "100%", height: "100%", imageRendering: "pixelated" }}
    />
  );
}

// ─── Helpers ────────────────────────────────────────────────────────────

function countDetections(detectionsArray) {
  const counts = { wall: 0, door: 0, window: 0, room: 0 };
  for (const d of detectionsArray) {
    if (counts[d.class] !== undefined) counts[d.class] += 1;
  }
  return {
    walls:    { count: counts.wall,   color: "var(--wall-color)" },
    doors:    { count: counts.door,   color: "var(--door-color)" },
    windows:  { count: counts.window, color: "var(--window-color)" },
    rooms:    { count: counts.room,   color: "var(--room-color)" },
    furniture:{ count: 0,             color: "var(--furniture-color)" },
  };
}

// ─── Error boundary ─────────────────────────────────────────────────────
// Wraps the 3D viewer specifically. Without this, any error thrown inside
// <Canvas> (e.g. GLTFLoader failing on a bad/missing model URL) is
// uncaught and crashes the ENTIRE React tree -- that's why the whole page
// was going black instead of just the 3D panel.
class ViewerErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error) {
    return { error };
  }
  componentDidUpdate(prevProps) {
    // Reset the boundary whenever a new model URL is tried, so retrying
    // an upload after a failure doesn't stay stuck on the old error.
    if (prevProps.resetKey !== this.props.resetKey && this.state.error) {
      this.setState({ error: null });
    }
  }
  render() {
    if (this.state.error) {
      return (
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "center",
          height: "100%", color: "#feb2b2", flexDirection: "column", gap: 8,
          padding: 24, textAlign: "center", fontSize: 13,
        }}>
          <div>⚠ Failed to load 3D model</div>
          <div style={{ opacity: 0.7, fontSize: 11 }}>{String(this.state.error.message || this.state.error)}</div>
        </div>
      );
    }
    return this.props.children;
  }
}

// ─── App ───────────────────────────────────────────────────────────────────

function App() {
  const [modelUrl, setModelUrl] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [activeControl, setActiveControl] = useState("rotate");

  const [detections, setDetections] = useState(DEFAULT_DETECTIONS);
  const [uploadedPreviewUrl, setUploadedPreviewUrl] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);   // null | "queued" | "detecting" | "reconstructing" | "done" | "failed"
  const [jobError, setJobError] = useState(null);
  const fileInputRef = useRef(null);
  const pollTimerRef = useRef(null);

  function stopPolling() {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }

  // Clean up the polling interval if the component ever unmounts mid-job.
  useEffect(() => () => stopPolling(), []);

  async function pollJob(jobId) {
    try {
      const res = await fetch(`${API_BASE}/api/plans/${jobId}`);
      if (!res.ok) throw new Error(`Status check failed (HTTP ${res.status})`);
      const data = await res.json();
      setJobStatus(data.status);

      if (data.status === "done") {
        stopPolling();
        setModelUrl(`${API_BASE}${data.model_url}`);

        if (data.detections_url) {
          const detRes = await fetch(`${API_BASE}${data.detections_url}`);
          if (detRes.ok) {
            const detArray = await detRes.json();
            setDetections(countDetections(detArray));
          }
        }
        setProcessing(false);
      } else if (data.status === "failed") {
        stopPolling();
        setJobError(data.error || "Reconstruction failed for an unknown reason.");
        setProcessing(false);
      }
      // else: still queued/detecting/reconstructing -- keep polling
    } catch (err) {
      stopPolling();
      setJobError(err.message);
      setProcessing(false);
    }
  }

  async function handleFileSelected(file) {
    if (!file) return;

    const allowed = ["image/png", "image/jpeg", "image/webp"];
    if (!allowed.includes(file.type)) {
      setJobError(`Unsupported file type: ${file.type || "unknown"}. Use PNG, JPG, or WEBP.`);
      return;
    }

    setJobError(null);
    setJobStatus("queued");
    setProcessing(true);
    setUploadedPreviewUrl(URL.createObjectURL(file));

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE}/api/plans`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ? JSON.stringify(body.detail) : `Upload failed (HTTP ${res.status})`);
      }
      const { job_id } = await res.json();

      pollTimerRef.current = setInterval(() => pollJob(job_id), 2000);
    } catch (err) {
      setJobError(err.message);
      setProcessing(false);
      setJobStatus(null);
    }
  }

  const statusLabel = {
    queued: "Queued…",
    detecting: "Running AI detection…",
    reconstructing: "Building 3D model…",
  }[jobStatus] || null;

  return (
    <div className="app-wrapper">
      {/* Header */}
      <header className="app-header">
        <div className="header-brand">
          <div className="brand-icon">🏠</div>
          <span className="brand-name">Plan2Scene AI</span>
          <span className="brand-version">v2.0</span>
        </div>
        <div className="header-status">
          <div className="status-dot" />
          {processing
            ? (statusLabel || "Processing…")
            : `Pipeline Ready · ${detections.rooms.count} Rooms · ${detections.walls.count} Walls · ${detections.doors.count + detections.windows.count} Openings`}
        </div>
      </header>

      {jobError && (
        <div style={{
          background: "#742a2a", color: "#feb2b2", padding: "8px 16px",
          fontSize: 13, textAlign: "center",
        }}>
          ⚠ {jobError}
        </div>
      )}

      {/* Main */}
      <div className="main-content">

        {/* ── Left Panel ── */}
        <aside className="left-panel">

          {/* 2D Floor Plan */}
          <div className="panel-section" style={{ flex: "0 0 45%" }}>
            <div className="panel-header">
              <span className="panel-title">Input: 2D Floor Plan</span>
              <button
                className="panel-badge"
                style={{ cursor: "pointer", border: "none" }}
                onClick={() => fileInputRef.current?.click()}
                disabled={processing}
              >
                {processing ? "Processing…" : "Upload"}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                style={{ display: "none" }}
                onChange={(e) => handleFileSelected(e.target.files?.[0])}
              />
            </div>
            <div className="floor-plan-container">
              {uploadedPreviewUrl ? (
                <img
                  src={uploadedPreviewUrl}
                  alt="Uploaded floor plan"
                  className="floor-plan-img"
                />
              ) : (
                <>
                  <img
                    src="/floorplan.png"
                    alt="2D Floor Plan"
                    className="floor-plan-img"
                    onError={(e) => { e.target.style.display = "none"; }}
                  />
                  <div className="floor-plan-placeholder">
                    <span className="icon">📐</span>
                    <p>No floor plan uploaded yet</p>
                    <p style={{ fontSize: "10px", marginTop: 4, opacity: 0.6 }}>
                      Click "Upload" above to select an image
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Detection Overlay + Legend */}
          <div className="panel-section" style={{ flex: "1" }}>
            <div className="panel-header">
              <span className="panel-title">AI Detection Overlay</span>
              <span className="panel-badge">YOLO v11</span>
            </div>

            <div className="detection-grid">
              <div className="legend-panel">
                <p className="legend-title">Detected Elements</p>
                {Object.entries(detections).map(([key, { count, color }]) => (
                  <div key={key} className="legend-item">
                    <div
                      className={`legend-color ${key}`}
                      style={{ background: color }}
                    />
                    <span style={{ textTransform: "capitalize" }}>{key}</span>
                    <span className="legend-count">{count}</span>
                  </div>
                ))}
              </div>

              <div className="overlay-canvas-wrapper">
                <DetectionOverlay />
              </div>
            </div>

            <div className="detection-stats">
              {[
                { id: "wall",   label: "Walls",   count: detections.walls.count },
                { id: "door",   label: "Doors",   count: detections.doors.count },
                { id: "window", label: "Windows", count: detections.windows.count },
                { id: "room",   label: "Rooms",   count: detections.rooms.count },
              ].map(({ id, label, count }) => (
                <div key={id} className="stat-item">
                  <div className={`stat-dot ${id}`} />
                  <span className="stat-count">{count}</span>
                  <span>{label}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>

        {/* ── Right Panel (3D Viewer) ── */}
        <section className="right-panel">
          <div className="viewer-header">
            <span className="viewer-title">Output: 3D Model</span>
            <div className="viewer-actions">
              <button className="action-btn" id="btn-export">Export</button>
              <button className="action-btn" id="btn-share">Share</button>
            </div>
          </div>

          <div className="canvas-wrapper">
            <div className="canvas-grid" />
            <ViewerErrorBoundary resetKey={modelUrl}>
              <ModelViewer
               activeControl={activeControl}
               setActiveControl={setActiveControl}
                 modelUrl={modelUrl}
              />
            </ViewerErrorBoundary>
          </div>

          {/* Controls bar */}
          <div className="controls-bar">
            <span className="controls-label">3D View Controls</span>
            {CONTROLS.map(({ id, icon, label }) => (
              <button
                key={id}
                id={`ctrl-${id}`}
                className={`ctrl-btn${activeControl === id ? " active" : ""}`}
                onClick={() => setActiveControl(id)}
                title={label}
              >
                <span className="icon">{icon}</span>
                {label}
              </button>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
export default App;