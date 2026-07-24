import { Canvas, useFrame } from "@react-three/fiber";
import {
  OrbitControls,
  useGLTF,
  Bounds,
  Center,
  Environment,
  Grid
} from "@react-three/drei";
import { useRef, useState, useEffect, useCallback } from "react";
import * as THREE from "three";

// ─── Model component ───────────────────────────────────────────────────────
function HouseModel({ wireframe, modelUrl }) {

  console.log("GLB PATH:", modelUrl);

  const { scene } = useGLTF(
  modelUrl || "/models/96066e7b.glb"
);

  useEffect(() => {
    scene.traverse((obj) => {
      if (obj.isMesh) {
        obj.material.wireframe = wireframe;
        obj.castShadow = true;
        obj.receiveShadow = true;
      }
    });
  }, [scene, wireframe]);

  return <primitive object={scene} />;
}

// ─── Camera controller exposed via ref ─────────────────────────────────────
function CameraController({ orbitRef, targetView }) {
  useFrame(({ camera }) => {
    if (targetView === "top") {
      camera.position.lerp(new THREE.Vector3(0, 3000, 0.001), 0.08);
      camera.lookAt(0, 0, 0);
    }
  });
  return (
    <OrbitControls
      ref={orbitRef}
      enableDamping
      dampingFactor={0.06}
      makeDefault
      minPolarAngle={0}
      maxPolarAngle={Math.PI / 2 + 0.1}
    />
  );
}

// ─── Scene ─────────────────────────────────────────────────────────────────
function Scene({ wireframe, modelUrl }) {
  return (
    <Bounds fit clip observe margin={1.1}>
      <Center>
        <HouseModel 
          wireframe={wireframe}
          modelUrl={modelUrl}
        />
      </Center>
    </Bounds>
  );
}

// ─── ModelViewer component ─────────────────────────────────────────────────
export default function ModelViewer({ 
  activeControl, 
  setActiveControl,
  modelUrl
}) {
    const orbitRef = useRef();
  const [wireframe, setWireframe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [targetView, setTargetView] = useState("orbit");

  const handleControl = useCallback(
    (id) => {
      setActiveControl(id);

      if (id === "wireframe") {
        setWireframe((v) => !v);
        return;
      }
      if (id === "realistic") {
        setWireframe(false);
        setTargetView("orbit");
        return;
      }
      if (id === "top") {
        setTargetView("top");
        return;
      }
      if (id === "rotate" || id === "pan" || id === "zoom") {
        setTargetView("orbit");
      }
    },
    [setActiveControl]
  );

  // Reset targetView after snapping to top so orbit works again
  useEffect(() => {
    if (targetView === "top") {
      const timer = setTimeout(() => setTargetView("orbit"), 1200);
      return () => clearTimeout(timer);
    }
  }, [targetView]);

  return (
    <Canvas
      shadows
      camera={{ position: [800, 600, 800], fov: 40 }}
      gl={{ antialias: true }}
      style={{ background: "transparent" }}
    >
      {/* Lighting */}
      <ambientLight intensity={1.4} />
      <directionalLight
        position={[1000, 2000, 800]}
        intensity={2.5}
        castShadow
        shadow-mapSize={[2048, 2048]}
      />
      <directionalLight position={[-800, 1000, -800]} intensity={0.8} />
      <hemisphereLight skyColor="#c4d4ff" groundColor="#080810" intensity={0.6} />

      {/* Grid floor */}
      <Grid
        args={[10000, 10000]}
        cellSize={100}
        cellThickness={0.3}
        cellColor="#1e2030"
        sectionSize={500}
        sectionThickness={0.6}
        sectionColor="#252840"
        fadeDistance={8000}
        position={[0, -2, 0]}
      />

      {/* House */}
      {/* House */}
<Scene 
  wireframe={wireframe}
  modelUrl={modelUrl}
/>

      {/* Camera controls */}
      <CameraController orbitRef={orbitRef} targetView={targetView} />
    </Canvas>
  );
}