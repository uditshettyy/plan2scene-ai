import React, { Suspense, useState, useMemo, useEffect, useRef } from "react";
import * as THREE from "three";
import { Canvas, useThree } from "@react-three/fiber";
import { OrbitControls, Environment, useGLTF } from "@react-three/drei";

const LAYER_NAMES = ["floor", "walls", "doors_windows", "stairs"];
const LAYER_LABELS = {
  floor: "Floor",
  walls: "Walls",
  doors_windows: "Doors & Windows",
  stairs: "Stairs",
};

// Computes the model's real bounding box after it loads and frames the
// camera to fit it, instead of relying on a hardcoded [400,400,400]
// position that only happens to work for one particular model size.
// Different floor plans have wildly different real-world scale (raw
// pixel coordinates from the source image), so a fixed camera position
// either starts inside the geometry (things get "eaten"/clipped) or
// absurdly far away, depending on the plan.
function useFitCameraOnLoad(scene, orbitRef, defaultViewRef) {
  const { camera } = useThree();
  const fitted = useRef(false);

  useEffect(() => {
    if (fitted.current || !scene) return;
    fitted.current = true;

    const box = new THREE.Box3().setFromObject(scene);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);

    const maxDim = Math.max(size.x, size.y, size.z, 1);
    const distance = maxDim * 1.4;
    const position = [center.x + distance, center.y + distance * 0.75, center.z + distance];

    camera.near = Math.max(0.1, maxDim / 1000);
    camera.far = distance * 20;
    camera.position.set(...position);
    camera.up.set(0, 1, 0);
    camera.lookAt(center);
    camera.updateProjectionMatrix();

    if (orbitRef.current) {
      orbitRef.current.target.copy(center);
      orbitRef.current.update();
    }

    // Remember this as "home", so the Top View button can return to it
    // instead of a generic hardcoded position.
    defaultViewRef.current = { position, target: [center.x, center.y, center.z] };
  }, [scene, camera, orbitRef, defaultViewRef]);
}

function House({ modelUrl, visibleLayers, wireframe, orbitRef, defaultViewRef }) {
  const { scene } = useGLTF(modelUrl);

  useMemo(() => {
    scene.traverse((child) => {
      if (LAYER_NAMES.includes(child.name)) {
        child.visible = visibleLayers.has(child.name);
      }
      if (child.isMesh && child.material) {
        const mats = Array.isArray(child.material) ? child.material : [child.material];
        mats.forEach((m) => { m.wireframe = wireframe; });
      }
    });
  }, [scene, visibleLayers, wireframe]);

  useFitCameraOnLoad(scene, orbitRef, defaultViewRef);

  return <primitive object={scene} />;
}

function LoadingFallback() {
  return (
    <mesh>
      <boxGeometry args={[0.1, 0.1, 0.1]} />
      <meshBasicMaterial wireframe color="#888" />
    </mesh>
  );
}

function LayerToggles({ visibleLayers, setVisibleLayers }) {
  const toggle = (layer) => {
    setVisibleLayers((prev) => {
      const next = new Set(prev);
      if (next.has(layer)) {
        next.delete(layer);
      } else {
        next.add(layer);
      }
      return next;
    });
  };

  return (
    <div
      style={{
        position: "absolute",
        top: 12,
        left: 12,
        background: "rgba(20, 20, 20, 0.7)",
        borderRadius: 8,
        padding: "10px 14px",
        color: "white",
        fontFamily: "system-ui, sans-serif",
        fontSize: 13,
        display: "flex",
        flexDirection: "column",
        gap: 6,
      }}
    >
      {LAYER_NAMES.map((layer) => (
        <label key={layer} style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={visibleLayers.has(layer)}
            onChange={() => toggle(layer)}
          />
          {LAYER_LABELS[layer]}
        </label>
      ))}
    </div>
  );
}

// Repositions the camera to a top-down view when activeControl === "top",
// and restores the auto-fitted "home" view (computed once the model
// loaded, see useFitCameraOnLoad) otherwise -- instead of a hardcoded
// position that doesn't match this particular model's real scale.
function CameraRig({ activeControl, orbitRef, defaultViewRef }) {
  const { camera } = useThree();
  const hasAppliedTop = useRef(false);

  useEffect(() => {
    const home = defaultViewRef.current;
    if (activeControl === "top") {
      const dist = Math.max(
        Math.abs(home.position[0] - home.target[0]),
        Math.abs(home.position[2] - home.target[2]),
        home.position[1]
      ) * 1.6;
      camera.position.set(home.target[0] + 0.01, home.target[1] + dist, home.target[2] + 0.01);
      camera.up.set(0, 0, -1);
      hasAppliedTop.current = true;
    } else if (hasAppliedTop.current) {
      camera.position.set(...home.position);
      camera.up.set(0, 1, 0);
      hasAppliedTop.current = false;
    } else {
      return; // nothing to do yet (initial mount, home view already applied by fit-on-load)
    }
    camera.lookAt(...home.target);
    if (orbitRef.current) {
      orbitRef.current.target.set(...home.target);
      orbitRef.current.update();
    }
  }, [activeControl, camera, orbitRef, defaultViewRef]);

  return null;
}

export default function ModelViewer({ modelUrl, activeControl, setActiveControl }) {
  const [visibleLayers, setVisibleLayers] = useState(new Set(LAYER_NAMES));
  const orbitRef = useRef();
  const defaultViewRef = useRef({ position: [400, 400, 400], target: [0, 0, 0] });
  const wireframe = activeControl === "wireframe";

  // No model to show yet (nothing uploaded/reconstructed) -- don't even
  // attempt a load. Loading a hardcoded fallback path here is what caused
  // the app to crash on first page open before any upload happened.
  if (!modelUrl) {
    return (
      <div style={{
        width: "100%", height: "100vh", background: "#1a1a1a",
        display: "flex", alignItems: "center", justifyContent: "center",
        color: "#8892a4", fontFamily: "system-ui, sans-serif", fontSize: 14,
      }}>
        Upload a floor plan to generate a 3D model
      </div>
    );
  }

  return (
    <div style={{ position: "relative", width: "100%", height: "100vh", background: "#1a1a1a" }}>
      <LayerToggles visibleLayers={visibleLayers} setVisibleLayers={setVisibleLayers} />
      {/* key={modelUrl} forces a full remount (fresh camera state) whenever
          a new model finishes reconstructing, instead of keeping stale
          camera/orbit position from whatever was loaded before it. */}
      <Canvas key={modelUrl} camera={{ position: [400, 400, 400], fov: 50, near: 1, far: 5000 }} shadows>
        <ambientLight intensity={0.6} />
        <directionalLight position={[300, 500, 200]} intensity={1.0} castShadow />
        <Suspense fallback={<LoadingFallback />}>
          <House
            modelUrl={modelUrl}
            visibleLayers={visibleLayers}
            wireframe={wireframe}
            orbitRef={orbitRef}
            defaultViewRef={defaultViewRef}
          />
          <Environment preset="apartment" />
        </Suspense>
        <CameraRig activeControl={activeControl} orbitRef={orbitRef} defaultViewRef={defaultViewRef} />
        <OrbitControls ref={orbitRef} makeDefault enableDamping dampingFactor={0.08} />
        <gridHelper args={[2000, 40, "#333", "#222"]} />
      </Canvas>
    </div>
  );
}