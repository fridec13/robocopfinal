<template>
  <div class="h-full flex overflow-hidden bg-gray-900">

    <!-- 좌측: Three.js 탑뷰 맵 -->
    <div ref="containerRef" class="flex-1 relative min-w-0">

      <!-- 로딩 -->
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center z-10">
        <div class="flex flex-col items-center gap-2 text-white">
          <div class="w-8 h-8 border-2 border-gray-500 border-t-blue-400 rounded-full animate-spin"></div>
          <span class="text-sm">GLB 모델 로딩중...</span>
        </div>
      </div>

      <!-- 조작 안내 -->
      <div class="absolute bottom-3 right-3 text-xs text-gray-400 bg-black bg-opacity-60 rounded px-2 py-1 pointer-events-none z-10 leading-5">
        <template v-if="interpMode">좌클릭: 꺾임점 추가 (자동 보간) | 우클릭 드래그: 이동 | 휠: 줌</template>
        <template v-else>좌클릭: 노드 추가 | 우클릭 드래그: 이동 | 휠: 줌</template>
      </div>

      <!-- 커서 좌표 미리보기 -->
      <div v-if="hoverUTM" class="absolute top-3 left-3 bg-black bg-opacity-70 text-xs text-cyan-300 font-mono rounded px-2 py-1 z-10 pointer-events-none">
        UTM: ({{ hoverUTM.x }}, {{ hoverUTM.y }})
      </div>

      <!-- 노드 수 표시 -->
      <div class="absolute top-3 right-3 bg-black bg-opacity-60 text-xs text-white rounded px-2 py-1 z-10 pointer-events-none space-y-0.5">
        <div>노드 {{ nodes.length }}개</div>
        <div v-if="interpMode" class="text-orange-300">꺾임점 {{ waypoints.length }}개</div>
      </div>
    </div>

    <!-- 우측: 노드 좌표 패널 -->
    <div class="w-80 flex-shrink-0 bg-gray-800 flex flex-col border-l border-gray-700">

      <!-- 헤더 -->
      <div class="px-4 py-3 bg-gray-900 border-b border-gray-700">
        <h2 class="text-white font-bold text-sm">맵 메이커</h2>
        <p class="text-gray-400 text-xs mt-0.5">
          <template v-if="interpMode">꺾임점만 찍으면 사이를 자동 분할합니다</template>
          <template v-else>GLB 모델 위를 클릭해 노드를 찍으세요</template>
        </p>
      </div>

      <!-- 모드 토글 + 간격 설정 -->
      <div class="px-3 py-2 border-b border-gray-700 space-y-2">
        <div class="flex items-center gap-2">
          <button
            @click="toggleInterpMode"
            class="flex-1 py-1.5 text-xs font-bold rounded transition-colors"
            :class="interpMode ? 'bg-orange-500 text-white' : 'bg-gray-600 text-gray-300 hover:bg-gray-500'"
          >
            {{ interpMode ? '🔶 자동 보간 모드 ON' : '⬜ 수동 모드' }}
          </button>
        </div>
        <div v-if="interpMode" class="flex items-center gap-2 text-xs text-gray-300">
          <span class="flex-shrink-0">보간 간격</span>
          <input
            v-model.number="interpDist"
            type="range" min="0.3" max="3.0" step="0.1"
            class="flex-1"
          />
          <span class="w-10 text-right font-mono text-orange-300">{{ interpDist.toFixed(1) }}m</span>
        </div>
        <div v-if="interpMode" class="text-xs text-gray-500">
          꺾임점 마지막 삭제: 보간 노드까지 함께 제거됩니다
        </div>
      </div>

      <!-- 버튼 -->
      <div class="px-3 py-2 flex gap-2 border-b border-gray-700 flex-wrap">
        <button @click="undoLast"
          class="px-2 py-1 text-xs bg-yellow-600 hover:bg-yellow-500 text-white rounded">
          ↩ 마지막 삭제
        </button>
        <button @click="clearAll"
          class="px-2 py-1 text-xs bg-red-700 hover:bg-red-600 text-white rounded">
          전체 삭제
        </button>
        <button @click="copyJSON"
          class="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-500 text-white rounded ml-auto">
          JSON 복사
        </button>
        <button @click="copyNodeList"
          class="px-2 py-1 text-xs bg-green-700 hover:bg-green-600 text-white rounded">
          노드만 복사
        </button>
      </div>

      <!-- 복사 완료 메시지 -->
      <div v-if="copyMsg" class="mx-3 mt-2 px-2 py-1 bg-green-800 text-green-300 text-xs rounded text-center">
        {{ copyMsg }}
      </div>

      <!-- 노드 목록 -->
      <div class="flex-1 overflow-y-auto px-3 py-2 space-y-1">
        <div v-if="nodes.length === 0" class="text-gray-500 text-xs text-center mt-8">
          아직 찍힌 노드가 없습니다
        </div>
        <div
          v-for="(node, i) in nodes"
          :key="i"
          class="flex items-center gap-2 bg-gray-700 rounded px-2 py-1.5 text-xs font-mono group"
        >
          <span class="text-yellow-400 font-bold w-6 text-right flex-shrink-0">{{ i + 1 }}</span>
          <span class="text-cyan-300 flex-1 truncate">
            [{{ node[0].toFixed(4) }}, {{ node[1].toFixed(4) }}]
          </span>
          <button @click="removeNode(i)" class="text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity">✕</button>
        </div>
      </div>

      <!-- JSON 미리보기 -->
      <div class="px-3 py-2 border-t border-gray-700">
        <p class="text-gray-400 text-xs mb-1">JSON 미리보기 (nodes 배열)</p>
        <div class="bg-gray-900 rounded p-2 max-h-32 overflow-y-auto text-xs font-mono text-green-300 whitespace-pre leading-4">{{ jsonPreview }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'

const UTM_ORIGIN_X = 304411.645
const UTM_ORIGIN_Y = 3892836.76
const GLB_OFFSET = new THREE.Vector3(2.4, 0, 4.7)

const containerRef = ref(null)
const loading = ref(true)
const nodes = ref([])        // [[utmX, utmY], ...] — 최종 노드 목록
const hoverUTM = ref(null)
const copyMsg = ref('')
const interpMode = ref(false)
const interpDist = ref(1.0)  // 보간 간격 (미터)

// 자동 보간 모드용
const waypoints = ref([])    // 꺾임점 목록 (scene Vector3)
// 각 꺾임점이 생성한 노드 범위: waypointNodeRanges[i] = { start, count }
let waypointNodeRanges = []

let scene, camera, renderer, controls
let glbMeshes = []
let groundPlane
let nodeSpheres = []       // 보간 노드 마커 (초록)
let waypointSpheres = []   // 꺾임점 마커 (주황)
let pathLines = []         // 꺾임점 간 선
let animFrameId

// scene → UTM 변환
const sceneToUTM = (sx, sz) => ({
  x: parseFloat((sx + UTM_ORIGIN_X).toFixed(6)),
  y: parseFloat((-sz + UTM_ORIGIN_Y).toFixed(6))
})

// UTM → scene 변환
const utmToScene = (ux, uy) => ({
  x: ux - UTM_ORIGIN_X,
  z: -(uy - UTM_ORIGIN_Y)
})

const init = () => {
  const el = containerRef.value
  const W = el.clientWidth
  const H = el.clientHeight

  // Scene
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x3a4a5a)

  // Orthographic camera (탑뷰)
  const aspect = W / H
  const viewSize = 30
  camera = new THREE.OrthographicCamera(
    -viewSize * aspect, viewSize * aspect,
    viewSize, -viewSize,
    0.1, 500
  )
  camera.position.set(0, 100, 0)
  camera.lookAt(0, 0, 0)

  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(W, H)
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  el.appendChild(renderer.domElement)

  // Controls — 패닝/줌만, 회전 없음
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableRotate = false
  controls.enablePan = true
  controls.zoomSpeed = 1.2
  controls.mouseButtons = {
    LEFT: null,
    MIDDLE: THREE.MOUSE.DOLLY,
    RIGHT: THREE.MOUSE.PAN
  }

  // 조명 — 탑뷰에서 벽 음영이 잘 보이도록 여러 방향 배치
  scene.add(new THREE.AmbientLight(0xffffff, 0.6))

  // 정수리 메인광 (그림자 생성)
  const dirTop = new THREE.DirectionalLight(0xffffff, 2.5)
  dirTop.position.set(5, 60, 5)
  dirTop.castShadow = true
  dirTop.shadow.mapSize.width = 2048
  dirTop.shadow.mapSize.height = 2048
  dirTop.shadow.camera.near = 1
  dirTop.shadow.camera.far = 200
  dirTop.shadow.camera.left = -50
  dirTop.shadow.camera.right = 50
  dirTop.shadow.camera.top = 50
  dirTop.shadow.camera.bottom = -50
  scene.add(dirTop)

  // 측면 보조광 (벽 윤곽 강조)
  const dirSide1 = new THREE.DirectionalLight(0xadd8ff, 1.2)
  dirSide1.position.set(40, 20, 0)
  scene.add(dirSide1)

  const dirSide2 = new THREE.DirectionalLight(0xffddaa, 0.8)
  dirSide2.position.set(-40, 20, -40)
  scene.add(dirSide2)

  const dirSide3 = new THREE.DirectionalLight(0xddffdd, 0.6)
  dirSide3.position.set(0, 20, 40)
  scene.add(dirSide3)


  // 바닥 평면 (raycasting 전용, 투명)
  const planeGeo = new THREE.PlaneGeometry(200, 200)
  const planeMat = new THREE.MeshBasicMaterial({ visible: false, side: THREE.DoubleSide })
  groundPlane = new THREE.Mesh(planeGeo, planeMat)
  groundPlane.rotation.x = -Math.PI / 2
  groundPlane.position.y = 0
  scene.add(groundPlane)

  // 원점 마커
  const originMat = new THREE.MeshBasicMaterial({ color: 0xff4444 })
  const originMesh = new THREE.Mesh(new THREE.SphereGeometry(0.3, 8, 8), originMat)
  originMesh.position.set(0, 0.5, 0)
  scene.add(originMesh)

  // GLB 로드
  const loader = new GLTFLoader()
  loader.load('/models/office.glb', (gltf) => {
    gltf.scene.position.copy(GLB_OFFSET)
    scene.add(gltf.scene)
    gltf.scene.traverse(obj => {
      if (obj.isMesh) {
        glbMeshes.push(obj)
        obj.castShadow = true
        obj.receiveShadow = true
      }
    })

    // 카메라를 모델 중앙으로 이동
    const box = new THREE.Box3().setFromObject(gltf.scene)
    const center = box.getCenter(new THREE.Vector3())
    controls.target.set(center.x, 0, center.z)
    camera.position.set(center.x, 100, center.z)
    controls.update()

    loading.value = false
  }, undefined, () => {
    loading.value = false
  })

  // 이벤트
  renderer.domElement.addEventListener('click', onLeftClick)
  renderer.domElement.addEventListener('mousemove', onMouseMove)
  window.addEventListener('resize', onResize)

  animate()
}

const getRaycastPoint = (event) => {
  const rect = renderer.domElement.getBoundingClientRect()
  const mouse = new THREE.Vector2(
    ((event.clientX - rect.left) / rect.width) * 2 - 1,
    -((event.clientY - rect.top) / rect.height) * 2 + 1
  )
  const raycaster = new THREE.Raycaster()
  raycaster.setFromCamera(mouse, camera)

  // GLB 메쉬 먼저
  if (glbMeshes.length) {
    const hits = raycaster.intersectObjects(glbMeshes, true)
    if (hits.length) return hits[0].point
  }
  // 바닥 평면 fallback
  const hits = raycaster.intersectObject(groundPlane)
  if (hits.length) return hits[0].point
  return null
}

const onMouseMove = (event) => {
  const pt = getRaycastPoint(event)
  if (pt) {
    hoverUTM.value = sceneToUTM(pt.x, pt.z)
  } else {
    hoverUTM.value = null
  }
}

const addNodeSphere = (pt, color = 0x00ffaa, radius = 0.25) => {
  const mesh = new THREE.Mesh(
    new THREE.SphereGeometry(radius, 8, 8),
    new THREE.MeshBasicMaterial({ color })
  )
  mesh.position.set(pt.x, pt.y + 0.3, pt.z)
  scene.add(mesh)
  return mesh
}

const addPathLine = (p1, p2) => {
  const geo = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(p1.x, p1.y + 0.35, p1.z),
    new THREE.Vector3(p2.x, p2.y + 0.35, p2.z)
  ])
  const line = new THREE.Line(geo, new THREE.LineBasicMaterial({ color: 0xff8800, linewidth: 2 }))
  scene.add(line)
  pathLines.push(line)
  return line
}

// 두 scene 점 사이를 interpDist 간격으로 보간 → UTM 노드 배열 반환
const interpolateBetween = (p1, p2) => {
  const dx = p2.x - p1.x
  const dz = p2.z - p1.z
  const dy = p2.y - p1.y
  const dist = Math.sqrt(dx * dx + dz * dz)
  const steps = Math.max(1, Math.floor(dist / interpDist.value))
  const result = []
  for (let i = 0; i <= steps; i++) {
    const t = i / steps
    const sx = p1.x + dx * t
    const sz = p1.z + dz * t
    const sy = p1.y + dy * t
    result.push({ scene: new THREE.Vector3(sx, sy, sz), utm: sceneToUTM(sx, sz) })
  }
  return result
}

const onLeftClick = (event) => {
  if (event.button !== 0) return
  const pt = getRaycastPoint(event)
  if (!pt) return

  if (interpMode.value) {
    // ── 자동 보간 모드 ──
    const wpSphere = addNodeSphere(pt, 0xff6600, 0.4)  // 주황 꺾임점 마커
    waypointSpheres.push(wpSphere)

    const prev = waypoints.value.length > 0 ? waypoints.value[waypoints.value.length - 1] : null
    waypoints.value.push(pt.clone())

    if (prev) {
      // 이전 꺾임점과 현재 사이 보간
      addPathLine(prev, pt)
      const interped = interpolateBetween(prev, pt)
      const startIdx = nodes.value.length
      // 첫 점은 이전 구간의 마지막 점과 겹치므로 i=1부터 추가 (첫 꺾임점은 예외)
      const startI = waypointNodeRanges.length > 0 ? 1 : 0
      interped.slice(startI).forEach(({ scene: sp, utm }) => {
        nodes.value.push([utm.x, utm.y])
        nodeSpheres.push(addNodeSphere(sp, 0x00ffaa, 0.2))
      })
      waypointNodeRanges.push({ start: startIdx, count: nodes.value.length - startIdx })
    } else {
      // 첫 꺾임점 — 노드 1개 추가
      const utm = sceneToUTM(pt.x, pt.z)
      nodes.value.push([utm.x, utm.y])
      nodeSpheres.push(addNodeSphere(pt, 0x00ffaa, 0.2))
      waypointNodeRanges.push({ start: 0, count: 1 })
    }
  } else {
    // ── 수동 모드 ──
    const utm = sceneToUTM(pt.x, pt.z)
    nodes.value.push([utm.x, utm.y])
    nodeSpheres.push(addNodeSphere(pt, 0x00ffaa, 0.25))
  }
}

const removeNode = (i) => {
  nodes.value.splice(i, 1)
  if (nodeSpheres[i]) { scene.remove(nodeSpheres[i]); nodeSpheres.splice(i, 1) }
}

const undoLast = () => {
  if (interpMode.value) {
    // 자동 보간 모드: 마지막 꺾임점 + 그 구간 노드 제거
    if (!waypoints.value.length) return
    waypoints.value.pop()
    const wpSphere = waypointSpheres.pop()
    if (wpSphere) scene.remove(wpSphere)

    const range = waypointNodeRanges.pop()
    if (range) {
      const removed = nodeSpheres.splice(range.start, range.count)
      removed.forEach(m => scene.remove(m))
      nodes.value.splice(range.start, range.count)
    }
    // 마지막 경로선 제거
    const line = pathLines.pop()
    if (line) scene.remove(line)
  } else {
    if (!nodes.value.length) return
    nodes.value.pop()
    const last = nodeSpheres.pop()
    if (last) scene.remove(last)
  }
}

const clearAll = () => {
  nodes.value = []
  waypoints.value = []
  waypointNodeRanges = []
  nodeSpheres.forEach(m => scene.remove(m)); nodeSpheres = []
  waypointSpheres.forEach(m => scene.remove(m)); waypointSpheres = []
  pathLines.forEach(l => scene.remove(l)); pathLines = []
}

const toggleInterpMode = () => {
  interpMode.value = !interpMode.value
  // 모드 전환 시 기존 작업 초기화
  clearAll()
}

// 노드 간 링크 생성 (순서대로 연결)
const buildJSON = () => {
  const nodeList = nodes.value.map(id => ({ id }))
  const links = []
  for (let i = 0; i < nodes.value.length - 1; i++) {
    const [x1, y1] = nodes.value[i]
    const [x2, y2] = nodes.value[i + 1]
    const cost = parseFloat(Math.hypot(x2 - x1, y2 - y1).toFixed(4))
    links.push({ cost, source: nodes.value[i], target: nodes.value[i + 1] })
  }
  return { directed: false, multigraph: false, graph: {}, nodes: nodeList, links }
}

const copyJSON = async () => {
  const json = JSON.stringify(buildJSON(), null, 2)
  await navigator.clipboard.writeText(json)
  showCopyMsg('전체 JSON 복사 완료!')
}

const copyNodeList = async () => {
  const txt = JSON.stringify(nodes.value.map(id => ({ id })), null, 2)
  await navigator.clipboard.writeText(txt)
  showCopyMsg('노드 목록 복사 완료!')
}

const showCopyMsg = (msg) => {
  copyMsg.value = msg
  setTimeout(() => { copyMsg.value = '' }, 2000)
}

const jsonPreview = computed(() => {
  if (!nodes.value.length) return '(노드 없음)'
  const preview = nodes.value.slice(0, 5).map(n => `  {"id": [${n[0].toFixed(3)}, ${n[1].toFixed(3)}]}`)
  const suffix = nodes.value.length > 5 ? `\n  ... 외 ${nodes.value.length - 5}개` : ''
  return `[\n${preview.join(',\n')}${suffix}\n]`
})

const animate = () => {
  animFrameId = requestAnimationFrame(animate)
  controls.update()
  renderer.render(scene, camera)
}

const onResize = () => {
  if (!containerRef.value) return
  const el = containerRef.value
  const W = el.clientWidth
  const H = el.clientHeight
  const aspect = W / H
  const viewSize = camera.top
  camera.left = -viewSize * aspect
  camera.right = viewSize * aspect
  camera.updateProjectionMatrix()
  renderer.setSize(W, H)
}

onMounted(() => { init() })
onUnmounted(() => {
  cancelAnimationFrame(animFrameId)
  renderer?.domElement.removeEventListener('click', onLeftClick)
  renderer?.domElement.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('resize', onResize)
  renderer?.dispose()
})
</script>
