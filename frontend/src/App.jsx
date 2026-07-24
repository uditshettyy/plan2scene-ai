import { useState, useRef, useEffect } from "react";
import ModelViewer from "./ModelViewer";
import "./App.css";

// ─── Detection data (from pipeline output) ────────────────────────────────
const DETECTIONS = {
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
function DetectionOverlay() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width;
    const H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    // Scale factor — the original image is ~4200×2481 px,
    // we only use the left half (x < 2000), so map [0,2000]×[660,2200] → canvas
    const srcW = 2000;
    const srcH = 1540;
    const srcX0 = 0;
    const srcY0 = 660;
    const sx = W / srcW;
    const sy = H / srcH;

    function px(x, y) {
      return [(x - srcX0) * sx, (y - srcY0) * sy];
    }

    // Walls (grey)
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

    // Rooms (green outlines)
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

    // Doors (orange rectangles)
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

    // Windows (blue rectangles)
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

    // Room labels
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


// ─── App ───────────────────────────────────────────────────────────────────
// ─── App ─────────────────────────────────────

// ─── App ───────────────────────────────

function App() {


  const [modelUrl, setModelUrl] = useState(
  "/models/96066e7b.glb"
);

  const [processing, setProcessing] = useState(false);

  const [activeControl, setActiveControl] = useState("rotate");

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
          Pipeline Ready · 4 Rooms · 14 Walls · 13 Openings
        </div>
      </header>

      {/* Main */}
      <div className="main-content">

        {/* ── Left Panel ── */}
        <aside className="left-panel">

          {/* 2D Floor Plan */}
          <div className="panel-section" style={{ flex: "0 0 45%" }}>
            <div className="panel-header">
              <span className="panel-title">Input: 2D Floor Plan</span>
              <span className="panel-badge">2481 × 4200px</span>
            </div>
            <div className="floor-plan-container">
              <img
                src="/floorplan.png"
                alt="2D Floor Plan"
                className="floor-plan-img"
                onError={(e) => { e.target.style.display = "none"; }}
              />
              <div className="floor-plan-placeholder">
                <span className="icon">📐</span>
                <p>test.png · 4200 × 2481</p>
                <p style={{ fontSize: "10px", marginTop: 4, opacity: 0.6 }}>
                  Place test.png in public/
                </p>
              </div>
            </div>
          </div>

          {/* Detection Overlay + Legend */}
          <div className="panel-section" style={{ flex: "1" }}>
            <div className="panel-header">
              <span className="panel-title">AI Detection Overlay</span>
              <span className="panel-badge">YOLO v11</span>
            </div>

            <div className="detection-grid">
              {/* Legend */}
              <div className="legend-panel">
                <p className="legend-title">Detected Elements</p>
                {Object.entries(DETECTIONS).map(([key, { count, color }]) => (
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

              {/* Overlay canvas */}
              <div className="overlay-canvas-wrapper">
                <DetectionOverlay />
              </div>
            </div>

            {/* Stats strip */}
            <div className="detection-stats">
              {[
                { id: "wall",   label: "Walls",   count: 14 },
                { id: "door",   label: "Doors",   count: 8 },
                { id: "window", label: "Windows", count: 5 },
                { id: "room",   label: "Rooms",   count: 4 },
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
            <ModelViewer
             activeControl={activeControl}
             setActiveControl={setActiveControl}
               modelUrl={modelUrl}
            />
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