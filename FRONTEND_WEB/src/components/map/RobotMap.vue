<template>
  <div class="flex flex-col bg-gray-900">
    <div class="flex-1 relative p-1">
      <div class="relative w-full h-[450px] min-h-[200px] mx-auto">
        <!-- Three.js 3D 맵 뷰어 -->
        <MapViewer3D
          ref="map3dRef"
          class="absolute inset-0 w-full h-full"
          :robot="props.robot"
          :is-monitoring-mode="props.isMonitoringMode"
          :map-nodes="mapData.nodes"
          :map-links="mapData.links"
          @node-click="handleNodeClick3D"
        />
      </div>

      <SelectedNodes 
        v-if="props.showSelectedNodes" 
        :selectedNodes="selectedNodesInfo" 
        @remove-node="handleNodeRemove"
      />

      <div v-if="loading" class="absolute inset-0 flex flex-col items-center justify-center bg-gray-900 bg-opacity-90 z-20">
        <div class="w-10 h-10 border-4 border-gray-600 border-t-blue-400 rounded-full animate-spin"></div>
        <span class="mt-3 text-gray-300 text-sm">맵 데이터 불러오는 중...</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import axios from 'axios'
import MapViewer3D from '@/components/map/MapViewer3D.vue'
import SelectedNodes from '@/components/map/SelectedNodes.vue'
import { useRobotsStore } from '@/stores/robots'
import { useRobotCommandsStore } from '@/stores/robotCommands'

// Store ????
const robotsStore = useRobotsStore()
const robotCommandsStore = useRobotCommandsStore()
const emit = defineEmits(['selectedNodesChange'])

// Refs
const map3dRef = ref(null)
const loading = ref(true)
const mapData = ref({ nodes: [], links: [] })
const selectedNodes = ref([])
const robotPositions = ref(new Map())

// Props ???
const props = defineProps({
  showSelectedNodes: {
    type: Boolean,
    default: true
  },
  robot: {
    type: Object,
    required: false,
    default: () => null
  },
  isMonitoringMode: {
    type: Boolean,
    default: false
  },
  showNodes: {
    type: Boolean,
    default: true
  }
})

// Computed
const currentRobotSeq = computed(() => {
  if (props.robot) return props.robot.seq
  const sel = robotsStore.selectedRobot
  if (sel) return robotsStore.robots.find(r => r.seq === sel)?.seq
  return null
})

const selectedNodesInfo = computed(() => {
  return selectedNodes.value.map(node => ({
    x: node.id[0].toFixed(2),
    y: node.id[1].toFixed(2)
  }))
})

// 3D 뷰어에 노드 클릭 전달
function handleNodeClick3D(nodes) {
  selectedNodes.value = nodes
  emit('selectedNodesChange', selectedNodes.value)
}

// ?? ??? ?????
async function handleNavigate() {
  try {
    await robotCommandsStore.navigateCommand(selectedNodes.value, currentRobotSeq.value)
    selectedNodes.value = []
    map3dRef.value?.resetNodeSelection()
    emit('selectedNodesChange', selectedNodes.value)
  } catch (error) {
    console.error('Navigation command failed:', error)
  }
}

async function handlePatrol() {
  try {
    await robotCommandsStore.patrolCommand(selectedNodes.value, currentRobotSeq.value)
    selectedNodes.value = []
    map3dRef.value?.resetNodeSelection()
    emit('selectedNodesChange', selectedNodes.value)
  } catch (error) {
    console.error('Patrol command failed:', error)
  }
}

async function resetSelection() {
  selectedNodes.value = await robotCommandsStore.resetSelectionCommand(currentRobotSeq.value)
  map3dRef.value?.resetNodeSelection()
}

async function handleTempStop() {
  await robotCommandsStore.tempStopCommand(currentRobotSeq.value)
}

async function handleResume() {
  await robotCommandsStore.resumeCommand(currentRobotSeq.value)
}

const handleNodeRemove = ({ node }) => {
  const index = selectedNodes.value.findIndex(n =>
    n.id[0].toFixed(2) === node.x && n.id[1].toFixed(2) === node.y
  )
  if (index !== -1) {
    selectedNodes.value = selectedNodes.value.filter((_, i) => i !== index)
    emit('selectedNodesChange', selectedNodes.value)
  }
}

// 맵 데이터 fetch
async function fetchMapData() {
  try {
    loading.value = true
    const response = await axios.get('/api/v1/map')
    mapData.value = { nodes: response.data.nodes, links: response.data.links }
  } catch (error) {
    console.error('맵 데이터 로드 오류:', error)
  } finally {
    loading.value = false
  }
}

// SSE 설정
function setupSSE() {
  if (robotPositions.value) robotPositions.value.clear()
  if (eventSources) {
    eventSources.forEach(s => s.close())
    eventSources.clear()
  }

  const newEventSources = new Map()
  const activeRobots = robotsStore.robots
    .filter(r => (r.seq === 1 || r.seq === 2) && (r?.isActive === true || r?.IsActive === true))

  activeRobots.forEach(robot => {
    const url = `/api/v1/robots/sse/${robot.seq}/down-utm`
    const es = new EventSource(url)
    let lastUpdate = 0

    es.onmessage = (event) => {
      try {
        const now = Date.now()
        if (now - lastUpdate < 300) return
        const data = JSON.parse(event.data)
        if (data?.position &&
            typeof data.position.x === 'number' &&
            typeof data.position.y === 'number' &&
            !isNaN(data.position.x) && !isNaN(data.position.y)) {
          robotPositions.value.set(robot.seq, { x: data.position.x, y: data.position.y })
          map3dRef.value?.updatePosition(robot.seq, data.position.x, data.position.y)
          lastUpdate = now
        }
      } catch (e) {
        console.error(`SSE parse error (robot ${robot.seq}):`, e)
      }
    }

    es.onerror = () => {
      es.close()
      robotPositions.value.delete(robot.seq)
      map3dRef.value?.clearPosition(robot.seq)
    }

    newEventSources.set(robot.seq, es)
  })

  return newEventSources
}

// Watchers
let eventSources = new Map()

watch(
  () => robotsStore.robots.map(r => r.seq).join(','),
  () => {
    eventSources.forEach(s => s.close())
    eventSources.clear()
    eventSources = setupSSE()
  }
)

watch(() => props.robot?.seq, (newSeq, oldSeq) => {
  if (newSeq && newSeq !== oldSeq) {
    selectedNodes.value = []
    map3dRef.value?.resetNodeSelection()
  }
})

// Lifecycle
onMounted(() => {
  fetchMapData()
  eventSources = setupSSE()
})

onUnmounted(() => {
  eventSources.forEach(s => s.close())
  eventSources.clear()
  robotPositions.value.clear()
})

defineExpose({
  handleNavigate,
  handlePatrol,
  resetSelection,
  handleTempStop,
  handleResume
})
</script>