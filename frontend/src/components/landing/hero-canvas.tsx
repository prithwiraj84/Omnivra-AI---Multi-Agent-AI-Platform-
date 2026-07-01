/**
 * HeroCanvas — a subtle, premium 3D ambient layer for the landing hero (react-three-fiber): a slowly
 * rotating sphere of ~2,600 glowing points (cyan→violet), with a faint sparkle field and gentle
 * mouse-parallax. It sits low-opacity BEHIND the product mockup as depth/texture — no distracting
 * centrepiece. Lazy-loaded + WebGL-guarded by the page; honors reduced motion; pauses off-screen.
 */
import { useMemo, useRef } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { Sparkles } from '@react-three/drei'
import * as THREE from 'three'

const CYAN = new THREE.Color('#22d3ee')
const VIOLET = new THREE.Color('#8b5cf6')

function PointSphere({ reduced }: { reduced: boolean }) {
  const ref = useRef<THREE.Points>(null)
  const { pointer } = useThree()

  const geometry = useMemo(() => {
    const N = 2600
    const radius = 2.5
    const positions = new Float32Array(N * 3)
    const colors = new Float32Array(N * 3)
    const golden = Math.PI * (1 + Math.sqrt(5))
    const col = new THREE.Color()
    for (let i = 0; i < N; i++) {
      const y = 1 - (i / (N - 1)) * 2 // -1..1
      const r = Math.sqrt(1 - y * y)
      const theta = golden * i
      const x = Math.cos(theta) * r
      const z = Math.sin(theta) * r
      positions.set([x * radius, y * radius, z * radius], i * 3)
      col.copy(CYAN).lerp(VIOLET, (y + 1) / 2)
      colors.set([col.r, col.g, col.b], i * 3)
    }
    const g = new THREE.BufferGeometry()
    g.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    g.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    return g
  }, [])

  useFrame((_, dt) => {
    const p = ref.current
    if (!p) return
    if (!reduced) {
      p.rotation.y += dt * 0.05
      p.rotation.x = THREE.MathUtils.lerp(p.rotation.x, pointer.y * 0.12, 0.04)
      p.rotation.z = THREE.MathUtils.lerp(p.rotation.z, pointer.x * -0.12, 0.04)
    }
  })

  return (
    <points ref={ref} geometry={geometry}>
      <pointsMaterial
        size={0.022}
        vertexColors
        transparent
        opacity={0.9}
        sizeAttenuation
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        toneMapped={false}
      />
    </points>
  )
}

export default function HeroCanvas({ reduced = false, active = true }: { reduced?: boolean; active?: boolean }) {
  return (
    <Canvas
      frameloop={!reduced && active ? 'always' : 'demand'}
      camera={{ position: [0, 0, 6], fov: 45 }}
      dpr={[1, 1.8]}
      gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      style={{ background: 'transparent' }}
    >
      <PointSphere reduced={reduced} />
      <Sparkles count={reduced ? 30 : 80} scale={11} size={2} speed={reduced ? 0 : 0.25} color="#22d3ee" opacity={0.5} />
    </Canvas>
  )
}
