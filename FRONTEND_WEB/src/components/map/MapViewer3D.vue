<template>
  <div ref="containerRef" class="relative w-full h-full bg-gray-900 overflow-hidden">
    <!-- 로딩 -->
    <div v-if="loading" class="absolute inset-0 flex items-center justify-center z-10">
      <div class="flex flex-col items-center gap-2 text-white">
        <div class="w-8 h-8 border-2 border-gray-500 border-t-blue-400 rounded-full animate-spin"></div>
        <span class="text-sm">3D 맵 로딩중...</span>
      </div>
    </div>

    <!-- 카메라 조작 안내 -->
    <div class="absolute bottom-3 right-3 text-xs text-gray-400 bg-black bg-opacity-50 rounded px-2 py-1 pointer-events-none z-10">
      마우스 드래그: 회전 | 휠: 줌 | 우클릭 드래그: 이동
    </div>

    <!-- 좌표계 디버그 패널 -->
    <div v-if="debugMode" class="absolute top-3 left-3 bg-black bg-opacity-75 text-xs rounded p-2 z-10 pointer-events-none leading-5 font-mono">
      <div class="text-yellow-300 font-bold mb-1">📐 좌표계 (Three.js 씬)</div>
      <div class="text-red-400">■ X (빨강) = East (+)</div>
      <div class="text-green-400">■ Y (초록) = Up</div>
      <div class="text-blue-400">■ Z (파랑) = South (+) = -North</div>
      <div class="text-gray-300 mt-1 border-t border-gray-600 pt-1">
        UTM→Scene 변환:<br/>
        scene.x = utm_x − {{ UTM_ORIGIN_X }}<br/>
        scene.z = −(utm_y − {{ UTM_ORIGIN_Y }})
      </div>
      <div v-if="debugCursor.visible" class="mt-1 border-t border-gray-600 pt-1 text-cyan-300">
        scene: x={{ debugCursor.x }}, y={{ debugCursor.y }}, z={{ debugCursor.z }}<br/>
        UTM: ({{ debugCursor.utmX }}, {{ debugCursor.utmY }})
      </div>
    </div>

    <!-- 디버그 토글 버튼 -->
    <button
      @click="debugMode = !debugMode"
      class="absolute bottom-3 left-3 text-xs px-2 py-1 rounded z-10"
      :class="debugMode ? 'bg-yellow-500 text-black' : 'bg-gray-700 text-gray-300'"
    >
      좌표계 {{ debugMode ? 'ON' : 'OFF' }}
    </button>

    <!-- 로봇 범례 -->
    <div v-if="robotLegends.length" class="absolute top-3 right-3 bg-black bg-opacity-60 rounded px-2 py-1 z-10 text-xs text-white space-y-1">
      <div v-for="r in robotLegends" :key="r.seq" class="flex items-center gap-2">
        <span class="w-3 h-3 rounded-full inline-block" :style="{ background: r.color }"></span>
        <span>{{ r.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { useRobotsStore } from '@/stores/robots'

// ── Props ─────────────────────────────────────────────────────────────────
const props = defineProps({
  robot: { type: Object, default: null },
  isMonitoringMode: { type: Boolean, default: false },
  mapNodes: { type: Array, default: () => [] },
  mapLinks: { type: Array, default: () => [] },
})
const emit = defineEmits(['nodeClick'])

const robotsStore = useRobotsStore()

// ── UTM ↔ 3D 좌표 변환 ────────────────────────────────────────────────────
// c101.world GPS origin: lat=35.1595, lon=126.8526 → UTM(304411.646, 3892842.473)
// Three.js 씬 좌표 = Gazebo 로컬 좌표 (미터 단위)
const UTM_ORIGIN_X = 304411.645
const UTM_ORIGIN_Y = 3892836.76
function utmToScene(utmX, utmY) {
  // Gazebo: +x=East, +y=North, Three.js: +x=East, +z=South (y=up)
  return {
    x: utmX - UTM_ORIGIN_X,
    z: -(utmY - UTM_ORIGIN_Y),
  }
}

// ── 로봇 색상 ──────────────────────────────────────────────────────────────
const ROBOT_COLORS = { 1: 0xff3333, 2: 0xffdd00, 3: 0x33ff33, 4: 0xff33ff, 5: 0x33aaff }
const robotLegends = computed(() =>
  Object.entries(robotPositions.value).map(([seq]) => {
    const robot = robotsStore.robots.find(r => r.seq === Number(seq))
    return {
      seq: Number(seq),
      color: '#' + (ROBOT_COLORS[Number(seq) % 6] || 0xffffff).toString(16).padStart(6, '0'),
      label: robot?.nickname || robot?.manufactureName || `로봇 ${seq}`,
    }
  })
)

// ── Refs ──────────────────────────────────────────────────────────────────
const containerRef = ref(null)
const loading = ref(true)
const robotPositions = ref({})  // { seq: { x, y } } in UTM
const debugMode = ref(false)
const debugCursor = ref({ visible: false, x: 0, z: 0, utmX: 0, utmY: 0 })

// ── Three.js 내부 객체 ─────────────────────────────────────────────────────
let scene, camera, renderer, controls, animFrame
let robotMeshes = {}        // { seq: THREE.Mesh }
let glbMeshes = []          // GLB 내부 메쉬 (디버그 클릭용)
let nodeMeshes = []
let linkLines = []
let selectedNodeSeqs = new Set()

// ── 씬 초기화 ─────────────────────────────────────────────────────────────
function initScene() {
  const el = containerRef.value
  const W = el.clientWidth || 800
  const H = el.clientHeight || 500

  // 렌더러
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.setSize(W, H)
  renderer.shadowMap.enabled = true
  el.appendChild(renderer.domElement)

  // 씬
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x1a1a2e)
  scene.fog = new THREE.FogExp2(0x1a1a2e, 0.015)

  // 카메라 (기울어진 조감도)
  camera = new THREE.PerspectiveCamera(50, W / H, 0.1, 1000)
  camera.position.set(0, 35, 25)
  camera.lookAt(0, 0, 0)

  // 컨트롤
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08
  controls.target.set(0, 0, 0)
  controls.maxPolarAngle = Math.PI / 2.1
  controls.minDistance = 5
  controls.maxDistance = 120

  // 조명
  const ambient = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambient)
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.8)
  dirLight.position.set(20, 40, 20)
  dirLight.castShadow = true
  scene.add(dirLight)

  // 좌표축 헬퍼 (X=빨강, Y=초록, Z=파랑), 길이 15m
  scene.add(new THREE.AxesHelper(15))

  // 원점 마커: 노란 구체 = UTM 기준점 (304411.646, 3892842.473)
  const originMarker = new THREE.Mesh(
    new THREE.SphereGeometry(0.4, 8, 8),
    new THREE.MeshBasicMaterial({ color: 0xffff00 })
  )
  originMarker.position.set(0, 0.5, 0)
  scene.add(originMarker)

  // GLB 시도 → 없으면 map.png fallback
  loadMap()

  // 렌더 루프
  function animate() {
    animFrame = requestAnimationFrame(animate)
    controls.update()
    renderer.render(scene, camera)
  }
  animate()
}

// ── 맵 로드 (GLB 우선, map.png fallback) ─────────────────────────────────
function loadMap() {
  const loader = new GLTFLoader()
  loader.load(
    '/models/office.glb',
    (gltf) => {
      // GLB 모델 위치 오프셋 (좌표계 정렬용)
      // Z offset 최대 2.2m까지 허용 (그 이상은 북쪽 노드가 건물 밖으로 나감)
      gltf.scene.position.set(2.4, 0, 1.5)
      scene.add(gltf.scene)
      // GLB 내부 메쉬 수집 (디버그 클릭용)
      gltf.scene.traverse(obj => {
        if (obj.isMesh) glbMeshes.push(obj)
      })
      // GLB 바운딩 박스 계산해서 카메라 포커스
      const box = new THREE.Box3().setFromObject(gltf.scene)
      const center = box.getCenter(new THREE.Vector3())
      controls.target.copy(center)
      camera.position.set(center.x, 35, center.z + 25)
      loading.value = false
    },
    undefined,
    () => {
      // GLB 없음 → map.png 텍스처 fallback
      buildFallbackMap()
      loading.value = false
    }
  )
}

// ── Fallback: map.png 텍스처 평면 ─────────────────────────────────────────
// 건물: 49.5m×22.5m, center=(-2.97, 11.25) in Gazebo
// → Three.js: x=-2.97, z=-11.25 (y-up 반전)
function buildFallbackMap() {
  const FLOOR_W = 49.5
  const FLOOR_H = 22.5
  const cx = -2.97
  const cz = -11.25  // Gazebo y → Three.js -z

  // map.png 텍스처 바닥
  const texLoader = new THREE.TextureLoader()
  texLoader.load(
    '/images/map-floor.png',
    (tex) => {
      tex.colorSpace = THREE.SRGBColorSpace
      const geo = new THREE.PlaneGeometry(FLOOR_W, FLOOR_H)
      const mat = new THREE.MeshLambertMaterial({ map: tex, side: THREE.DoubleSide })
      const plane = new THREE.Mesh(geo, mat)
      plane.rotation.x = -Math.PI / 2
      plane.position.set(cx, 0, cz)
      plane.receiveShadow = true
      scene.add(plane)

      // 그리드 오버레이
      const grid = new THREE.GridHelper(60, 30, 0x333366, 0x222244)
      grid.position.set(cx, 0.01, cz)
      scene.add(grid)

      // 카메라 포커스를 맵 중심으로
      controls.target.set(cx, 0, cz)
      camera.position.set(cx, 35, cz + 25)
    },
    undefined,
    () => {
      // 텍스처도 없으면 단색 바닥
      const geo = new THREE.PlaneGeometry(FLOOR_W, FLOOR_H)
      const mat = new THREE.MeshLambertMaterial({ color: 0x2a2a4a })
      const plane = new THREE.Mesh(geo, mat)
      plane.rotation.x = -Math.PI / 2
      plane.position.set(cx, 0, cz)
      scene.add(plane)
    }
  )
}

// ── 경로 노드 & 링크 렌더링 ────────────────────────────────────────────────
function renderMapData() {
  // 기존 노드/링크 제거
  nodeMeshes.forEach(m => scene.remove(m))
  linkLines.forEach(l => scene.remove(l))
  nodeMeshes = []
  linkLines = []

  if (!props.mapNodes.length) return

  // 노드 구체
  const nodeGeo = new THREE.SphereGeometry(0.25, 8, 8)
  props.mapNodes.forEach(node => {
    const sc = utmToScene(node.id[0], node.id[1])
    const isSelected = selectedNodeSeqs.has(`${node.id[0]},${node.id[1]}`)
    const mat = new THREE.MeshLambertMaterial({
      color: isSelected ? 0xff4081 : 0x007bff,
      emissive: isSelected ? 0xff2060 : 0x002266,
    })
    const mesh = new THREE.Mesh(nodeGeo, mat)
    mesh.position.set(sc.x, 0.3, sc.z)
    mesh.userData = { node }
    scene.add(mesh)
    nodeMeshes.push(mesh)
  })

  // 링크 선
  const lineMat = new THREE.LineBasicMaterial({ color: 0x4488ff, transparent: true, opacity: 0.7 })
  props.mapLinks.forEach(link => {
    const a = utmToScene(link.source[0], link.source[1])
    const b = utmToScene(link.target[0], link.target[1])
    const geo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(a.x, 0.15, a.z),
      new THREE.Vector3(b.x, 0.15, b.z),
    ])
    const line = new THREE.Line(geo, lineMat)
    scene.add(line)
    linkLines.push(line)
  })
}

// ── 로봇 마커 업데이트 ────────────────────────────────────────────────────
function updateRobotMarkers() {
  const seqs = Object.keys(robotPositions.value)

  // 기존 마커 중 없어진 것 제거
  Object.keys(robotMeshes).forEach(seq => {
    if (!robotPositions.value[seq]) {
      scene.remove(robotMeshes[seq])
      delete robotMeshes[seq]
    }
  })

  seqs.forEach(seq => {
    const pos = robotPositions.value[seq]
    if (!pos || isNaN(pos.x) || isNaN(pos.y)) return
    const sc = utmToScene(pos.x, pos.y)
    const color = ROBOT_COLORS[Number(seq) % 6] || 0xffffff

    if (!robotMeshes[seq]) {
      // 처음 → 원뿔(로봇 모양) 생성
      const geo = new THREE.ConeGeometry(0.5, 1.5, 8)
      const mat = new THREE.MeshLambertMaterial({ color, emissive: color, emissiveIntensity: 0.4 })
      const mesh = new THREE.Mesh(geo, mat)
      // 원뿔 아래쪽이 앞방향이 되도록 기본 회전
      mesh.rotation.x = Math.PI  // 뾰족한 쪽 위로
      robotMeshes[seq] = mesh

      // 후광 포인트 라이트
      const light = new THREE.PointLight(color, 1.5, 6)
      mesh.add(light)
      scene.add(mesh)
    }

    robotMeshes[seq].position.set(sc.x, 1.0, sc.z)
  })
}

// ── 노드 클릭 (raycasting) ────────────────────────────────────────────────
function onClick(e) {
  // 휠클릭(button=1)은 디버그 전용, 좌클릭(button=0)은 노드 선택
  if (e.button === 1) e.preventDefault()
  if (e.button !== 0 && e.button !== 1) return
  const isDebugClick = e.button === 1
  if (!isDebugClick && props.isMonitoringMode) return
  const el = containerRef.value
  const rect = el.getBoundingClientRect()
  const mouse = new THREE.Vector2(
    ((e.clientX - rect.left) / rect.width) * 2 - 1,
    -((e.clientY - rect.top) / rect.height) * 2 + 1
  )
  const raycaster = new THREE.Raycaster()
  raycaster.setFromCamera(mouse, camera)
  // 디버그 모드: 휠클릭으로 GLB 메쉬 → 바닥 평면 좌표 표시
  if (debugMode.value && isDebugClick) {
    let hit3D = null

    // 1순위: GLB 메쉬 표면 교차
    const glbHits = raycaster.intersectObjects(glbMeshes, false)
    if (glbHits.length) {
      hit3D = glbHits[0].point
    } else {
      // 2순위: Y=0 바닥 평면 교차
      const groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0)
      const pt = new THREE.Vector3()
      if (raycaster.ray.intersectPlane(groundPlane, pt)) hit3D = pt
    }

    if (hit3D) {
      debugCursor.value = {
        visible: true,
        x: Math.round(hit3D.x * 100) / 100,
        y: Math.round(hit3D.y * 100) / 100,
        z: Math.round(hit3D.z * 100) / 100,
        utmX: Math.round((hit3D.x + UTM_ORIGIN_X) * 100) / 100,
        utmY: Math.round((-hit3D.z + UTM_ORIGIN_Y) * 100) / 100,
      }
    }
  }

  if (isDebugClick) return  // 휠클릭은 디버그 전용, 노드 선택 안 함
  const hits = raycaster.intersectObjects(nodeMeshes)
  if (hits.length) {
    const node = hits[0].object.userData.node
    const key = `${node.id[0]},${node.id[1]}`
    if (selectedNodeSeqs.has(key)) selectedNodeSeqs.delete(key)
    else selectedNodeSeqs.add(key)
    emit('nodeClick', [...selectedNodeSeqs].map(k => {
      const [x, y] = k.split(',').map(Number)
      return props.mapNodes.find(n => n.id[0] === x && n.id[1] === y)
    }).filter(Boolean))
    renderMapData()
  }
}

// ── 리사이즈 ──────────────────────────────────────────────────────────────
let _resizeObs
function onResize() {
  if (!containerRef.value || !renderer) return
  const W = containerRef.value.clientWidth
  const H = containerRef.value.clientHeight
  camera.aspect = W / H
  camera.updateProjectionMatrix()
  renderer.setSize(W, H)
}

// ── 외부 데이터 업데이트 API ───────────────────────────────────────────────
function updatePosition(seq, utmX, utmY) {
  robotPositions.value = { ...robotPositions.value, [seq]: { x: utmX, y: utmY } }
  updateRobotMarkers()
}
function clearPosition(seq) {
  const next = { ...robotPositions.value }
  delete next[seq]
  robotPositions.value = next
  updateRobotMarkers()
}
function resetNodeSelection() {
  selectedNodeSeqs.clear()
  renderMapData()
}

defineExpose({ updatePosition, clearPosition, resetNodeSelection })

// ── Watch ──────────────────────────────────────────────────────────────────
watch(() => [props.mapNodes, props.mapLinks], renderMapData, { deep: true })

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(() => {
  initScene()
  containerRef.value.addEventListener('mousedown', onClick)
  _resizeObs = new ResizeObserver(onResize)
  _resizeObs.observe(containerRef.value)
})

onUnmounted(() => {
  cancelAnimationFrame(animFrame)
  renderer?.dispose()
  controls?.dispose()
  _resizeObs?.disconnect()
  containerRef.value?.removeEventListener('mousedown', onClick)
})
</script>
