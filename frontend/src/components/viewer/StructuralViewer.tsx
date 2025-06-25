'use client'

import React, { useRef, useState, useEffect } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Grid, Sphere, Line, Text, Box } from '@react-three/drei'
import { Vector3, BufferGeometry, Float32BufferAttribute } from 'three'
import * as THREE from 'three'

interface Node {
  id: number
  label: string
  position: [number, number, number]
}

interface Element {
  id: number
  label: string
  type: string
  start_node: number
  end_node: number
  material_type: string
  section_id: number
}

interface StructuralModel {
  nodes: Node[]
  elements: Element[]
  materials: Record<string, any>
  analysis_results?: any
}

interface StructuralViewerProps {
  model: StructuralModel
  showNodes?: boolean
  showElements?: boolean
  showLabels?: boolean
  showDeformed?: boolean
  colorByMaterial?: boolean
  onElementClick?: (elementId: number) => void
  onNodeClick?: (nodeId: number) => void
}

// Node component
function StructuralNode({ 
  node, 
  showLabel, 
  onClick 
}: { 
  node: Node
  showLabel: boolean
  onClick?: (nodeId: number) => void 
}) {
  const meshRef = useRef<THREE.Mesh>(null)
  const [hovered, setHovered] = useState(false)

  return (
    <group position={node.position}>
      <Sphere
        ref={meshRef}
        args={[0.05, 8, 8]}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
        onClick={() => onClick?.(node.id)}
      >
        <meshStandardMaterial 
          color={hovered ? '#ff6b6b' : '#4ecdc4'} 
          transparent
          opacity={0.8}
        />
      </Sphere>
      {showLabel && (
        <Text
          position={[0, 0.2, 0]}
          fontSize={0.1}
          color="#333"
          anchorX="center"
          anchorY="middle"
        >
          {node.label}
        </Text>
      )}
    </group>
  )
}

// Element component
function StructuralElement({ 
  element, 
  nodes, 
  materials, 
  colorByMaterial, 
  showLabel,
  onClick 
}: {
  element: Element
  nodes: Node[]
  materials: Record<string, any>
  colorByMaterial: boolean
  showLabel: boolean
  onClick?: (elementId: number) => void
}) {
  const lineRef = useRef<THREE.Line>(null)
  const [hovered, setHovered] = useState(false)

  const startNode = nodes.find(n => n.id === element.start_node)
  const endNode = nodes.find(n => n.id === element.end_node)

  if (!startNode || !endNode) return null

  // Calculate element geometry
  const start = new Vector3(...startNode.position)
  const end = new Vector3(...endNode.position)
  const direction = end.clone().sub(start).normalize()
  const length = start.distanceTo(end)
  const midPoint = start.clone().add(end).multiplyScalar(0.5)

  // Get material color
  const getMaterialColor = () => {
    if (!colorByMaterial) return hovered ? '#feca57' : '#4ecdc4'
    
    const materialColors: Record<string, string> = {
      concrete: '#808080',
      steel: '#b87333',
      timber: '#8b4513',
      composite: '#4a90e2'
    }
    
    return materialColors[element.material_type] || '#4ecdc4'
  }

  // Create line geometry
  const points = [start, end]
  const lineGeometry = new BufferGeometry().setFromPoints(points)

  return (
    <group>
      <Line
        points={[start, end]}
        color={getMaterialColor()}
        lineWidth={hovered ? 3 : 2}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
        onClick={() => onClick?.(element.id)}
      />
      
      {/* Element as cylinder for better 3D visualization */}
      <group position={midPoint.toArray()}>
        <Box
          args={[0.05, 0.05, length]}
          rotation={[0, 0, Math.atan2(direction.y, direction.x)]}
          onPointerOver={() => setHovered(true)}
          onPointerOut={() => setHovered(false)}
          onClick={() => onClick?.(element.id)}
        >
          <meshStandardMaterial 
            color={getMaterialColor()} 
            transparent
            opacity={hovered ? 0.9 : 0.7}
          />
        </Box>
        
        {showLabel && (
          <Text
            position={[0, 0.2, 0]}
            fontSize={0.08}
            color="#333"
            anchorX="center"
            anchorY="middle"
          >
            {element.label}
          </Text>
        )}
      </group>
    </group>
  )
}

// Deformed shape component
function DeformedShape({ 
  model, 
  displacements, 
  scale 
}: {
  model: StructuralModel
  displacements: Record<string, any>
  scale: number
}) {
  const deformedNodes = model.nodes.map(node => {
    const disp = displacements[node.id.toString()]
    if (!disp) return node

    return {
      ...node,
      position: [
        node.position[0] + (disp.ux || 0) * scale,
        node.position[1] + (disp.uy || 0) * scale,
        node.position[2] + (disp.uz || 0) * scale
      ] as [number, number, number]
    }
  })

  return (
    <group>
      {model.elements.map(element => {
        const startNode = deformedNodes.find(n => n.id === element.start_node)
        const endNode = deformedNodes.find(n => n.id === element.end_node)

        if (!startNode || !endNode) return null

        const points = [
          new Vector3(...startNode.position),
          new Vector3(...endNode.position)
        ]
        const lineGeometry = new BufferGeometry().setFromPoints(points)

        return (
          <Line 
            key={`deformed-${element.id}`} 
            points={points}
            color="#ff9ff3"
            lineWidth={2}
          />
        )
      })}
    </group>
  )
}

// Analysis results visualization
function AnalysisResults({ 
  model, 
  analysisData 
}: {
  model: StructuralModel
  analysisData: any
}) {
  if (!analysisData || !analysisData.displacements) return null

  // Calculate displacement magnifications for visualization
  const maxDisplacement = Math.max(
    ...Object.values(analysisData.displacements).map((disp: any) => {
      if (!disp) return 0
      return Math.sqrt((disp.ux || 0)**2 + (disp.uy || 0)**2 + (disp.uz || 0)**2)
    })
  )

  const modelSize = model.nodes.reduce((max, node) => {
    const distance = Math.sqrt(node.position[0]**2 + node.position[1]**2 + node.position[2]**2)
    return Math.max(max, distance)
  }, 0)

  const scale = maxDisplacement > 0 ? (modelSize * 0.1) / maxDisplacement : 1

  return (
    <DeformedShape 
      model={model} 
      displacements={analysisData.displacements} 
      scale={scale} 
    />
  )
}

// Main viewer component
function ViewerScene({ 
  model, 
  showNodes, 
  showElements, 
  showLabels, 
  showDeformed, 
  colorByMaterial,
  onElementClick,
  onNodeClick 
}: StructuralViewerProps) {
  const { camera } = useThree()

  useEffect(() => {
    // Auto-fit camera to model
    if (model.nodes.length > 0) {
      const positions = model.nodes.map(n => new Vector3(...n.position))
      const box = new THREE.Box3().setFromPoints(positions)
      const center = box.getCenter(new Vector3())
      const size = box.getSize(new Vector3())
      
      const maxDim = Math.max(size.x, size.y, size.z)
      const fov = (camera as THREE.PerspectiveCamera).fov * (Math.PI / 180)
      const distance = maxDim / (2 * Math.tan(fov / 2)) * 1.5

      camera.position.set(
        center.x + distance,
        center.y + distance,
        center.z + distance
      )
      camera.lookAt(center)
    }
  }, [model, camera])

  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.6} />
      <directionalLight position={[10, 10, 5]} intensity={0.8} />
      <pointLight position={[-10, -10, -5]} intensity={0.4} />

      {/* Grid */}
      <Grid
        args={[50, 50]}
        cellSize={1}
        cellThickness={0.5}
        cellColor="#e0e0e0"
        sectionSize={5}
        sectionThickness={1}
        sectionColor="#808080"
        fadeDistance={100}
        fadeStrength={1}
      />

      {/* Structural nodes */}
      {showNodes && model.nodes.map(node => (
        <StructuralNode
          key={node.id}
          node={node}
          showLabel={showLabels || false}
          onClick={onNodeClick}
        />
      ))}

      {/* Structural elements */}
      {showElements && model.elements.map(element => (
        <StructuralElement
          key={element.id}
          element={element}
          nodes={model.nodes}
          materials={model.materials}
          colorByMaterial={colorByMaterial || false}
          showLabel={showLabels || false}
          onClick={onElementClick}
        />
      ))}

      {/* Analysis results */}
      {showDeformed && model.analysis_results && (
        <AnalysisResults 
          model={model} 
          analysisData={model.analysis_results} 
        />
      )}

      {/* Controls */}
      <OrbitControls
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        dampingFactor={0.05}
        enableDamping={true}
      />
    </>
  )
}

// Main component
export default function StructuralViewer(props: StructuralViewerProps) {
  const {
    model,
    showNodes = true,
    showElements = true,
    showLabels = false,
    showDeformed = false,
    colorByMaterial = true,
    onElementClick,
    onNodeClick
  } = props

  if (!model || !model.nodes || !model.elements) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="spinner mb-4"></div>
          <p className="text-gray-600">Loading structural model...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full h-full relative">
      <Canvas
        camera={{ position: [10, 10, 10], fov: 60 }}
        gl={{ antialias: true, alpha: false }}
        dpr={[1, 2]}
      >
        <ViewerScene
          model={model}
          showNodes={showNodes}
          showElements={showElements}
          showLabels={showLabels}
          showDeformed={showDeformed}
          colorByMaterial={colorByMaterial}
          onElementClick={onElementClick}
          onNodeClick={onNodeClick}
        />
      </Canvas>
      
      {/* Viewer controls overlay */}
      <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg">
        <div className="text-sm text-gray-600">
          <div>Nodes: {model.nodes.length}</div>
          <div>Elements: {model.elements.length}</div>
          {model.analysis_results && (
            <div className="mt-2 pt-2 border-t">
              <div className="text-green-600">Analysis: {model.analysis_results.type}</div>
            </div>
          )}
        </div>
      </div>

      {/* Legend */}
      {colorByMaterial && (
        <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg">
          <h4 className="text-sm font-medium mb-2">Materials</h4>
          <div className="space-y-1 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-gray-500 rounded"></div>
              <span>Concrete</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-amber-600 rounded"></div>
              <span>Steel</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-amber-800 rounded"></div>
              <span>Timber</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-500 rounded"></div>
              <span>Composite</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
