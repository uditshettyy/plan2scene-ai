import { Canvas } from "@react-three/fiber";
import {
  OrbitControls,
  useGLTF,
  Bounds,
  Center
} from "@react-three/drei";


function HouseModel(){

  const { scene } = useGLTF(
    "/models/plan2scene_house.glb"
  );


  return (
    <primitive
      object={scene}
    />
  );
}



function Scene(){

  return (
    <Bounds
      fit
      clip
      observe
      margin={1.0}
    >

      <Center>
        <HouseModel/>
      </Center>

    </Bounds>
  );

}



export default function ModelViewer(){

  return (

    <Canvas
      camera={{
        position:[2500,2200,2500],
        fov:35
      }}
    >


      <ambientLight intensity={1.8}/>


      <directionalLight
        position={[1000,3000,1000]}
        intensity={4}
      />


      <directionalLight
        position={[-2000,2000,-2000]}
        intensity={1}
      />
      <OrbitControls
 minPolarAngle={0.3}
 maxPolarAngle={1.4}
/>


      <gridHelper
        args={[5000,100]}
        position={[100,-2,-13]}
      />


      <Scene/>


      <OrbitControls
        enableDamping
        makeDefault
      />


    </Canvas>

  );
}