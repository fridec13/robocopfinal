<template>
  <div class="flex flex-col bg-white">
    <div class="flex-1 relative p-1">
      <div class="relative w-full h-[450px] min-h-[20px] mx-auto" ref="containerRef">
        <v-chart
          class="absolute inset-0 w-full h-full"
          :option="chartOption"
          ref="chartRef"
          autoresize
          @click="handleNodeClick"
          @finished="updateBgImage"
        />
      </div>

      <SelectedNodes 
        v-if="props.showSelectedNodes" 
        :selectedNodes="selectedNodesInfo" 
        @remove-node="handleNodeRemove"
      />

      <div v-if="loading" class="absolute inset-0 flex flex-col items-center justify-center bg-white bg-opacity-90">
        <div class="w-10 h-10 border-4 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
        <span class="mt-3 text-gray-700">????????? ????? ??..</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import axios from 'axios'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { GraphicComponent, GridComponent, TooltipComponent, ToolboxComponent } from 'echarts/components'
import { ScatterChart, LinesChart } from 'echarts/charts'
import VChart from 'vue-echarts'
import SelectedNodes from '@/components/map/SelectedNodes.vue'
import { useRobotsStore } from '@/stores/robots'
import { useRobotCommandsStore } from '@/stores/robotCommands'

use([
  CanvasRenderer,
  GraphicComponent,
  GridComponent,
  TooltipComponent,
  ToolboxComponent,
  ScatterChart,
  LinesChart
])

// Store ????
const robotsStore = useRobotsStore()
const robotCommandsStore = useRobotCommandsStore()
const emit = defineEmits(['selectedNodesChange'])

// map.png UTM extent (c101.world GPS origin + map.yaml 계산)
// c101 GPS origin: lat=35.1595, lon=126.8526 → UTM(304411.646, 3892842.473)
// map.yaml: origin=(-30,-30), resolution=0.05 m/px, size=1200×1200px → 60m×60m
const MAP_UTM = {
  xMin: 304381.65,
  xMax: 304441.65,
  yMin: 3892812.47,
  yMax: 3892872.47,
}

// Refs ???
const containerRef = ref(null)
const chartRef = ref(null)
const loading = ref(true)
const mapData = ref({ nodes: [], links: [] })
const selectedNodes = ref([])
const imageWidth = ref(800)
const imageHeight = ref(500)
const robotPositions = ref(new Map()) // ??? ????????????????Map
let _lastBgPos = null

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

// Robot colors for monitoring mode
const robotColors = {
  0: '#0000ff',
  1: '#ffff00',
  2: '#00ff00',
  3: '#ff00ff',
  4: '#ff0000'
}

// Computed ???
const currentRobotSeq = computed(() => {
  if (props.robot) {
    return props.robot.seq
  }

  const selectedRobotSeq = robotsStore.selectedRobot
  if (selectedRobotSeq) {
    const selectedRobot = robotsStore.robots.find(
      robot => robot.seq === selectedRobotSeq
    )
    return selectedRobot?.seq
  }
  return null
})

const selectedNodesInfo = computed(() => {
  return selectedNodes.value.map(node => ({
    x: node.id[0].toFixed(2),
    y: node.id[1].toFixed(2)
  }))
})

// ?? ??? computed
const chartOption = computed(() => {
  const robotSeries = []
  
  // ?? ?? ??? ???
  if (robotPositions.value) {
    robotPositions.value.forEach((position, robotSeq) => {
      // position??????? x, y?? ?? ??? ????? ??
      if (position && 
          position.x != null && 
          position.y != null &&
          !isNaN(position.x) && 
          !isNaN(position.y)) {
        const isSelectedRobot = !props.isMonitoringMode && robotSeq === currentRobotSeq.value;
        
        robotSeries.push({
          type: 'scatter',
          data: [[position.x, position.y]],
          symbolSize: 15,
          itemStyle: {
            color: isSelectedRobot ? '#ff0000' : robotColors[robotSeq % Object.keys(robotColors).length]
          },
          symbol: 'circle',
          zlevel: 3
        });
      }
    });
  }

  return {
    animation: false,
    backgroundColor: '#fff',
    grid: {
      left: '5%',
      right: '5%',
      top: '5%',
      bottom: '5%',
      containLabel: true
    },
    graphic: [],
    tooltip: {
      show: true,
      trigger: 'item',
      confine: true,
      enterable: false,
      axisPointer: {
        type: 'none'
      },
      formatter: function(params) {
        // null check for params and data
        if (!params || !params.data) return '';
        
        try {
          // ?? ????? ??
          if (params.seriesIndex < robotSeries.length && robotPositions.value) {
            const robotSeqArray = Array.from(robotPositions.value.keys());
            if (!robotSeqArray || robotSeqArray.length === 0) return '';
            
            const robotSeq = robotSeqArray[params.seriesIndex];
            if (!robotSeq) return '';
            
            const robot = robotsStore.robots.find(r => r.seq === robotSeq);
            return robot ? `??: ${robot.nickname || robot.manufactureName || robotSeq}` : '';
          }
          
          // ??? ????? ?? - monitoring mode? ??? ??? ?? ???
          if (!props.isMonitoringMode && params.componentSubType === 'scatter' && Array.isArray(params.data)) {
            const x = Number(params.data[0]);
            const y = Number(params.data[1]);
            
            if (isNaN(x) || isNaN(y)) return '';
            return `??: (${x.toFixed(2)}, ${y.toFixed(2)})`;
          }
          
          return '';
        } catch (error) {
          console.error('Tooltip formatter error:', error);
          return '';
        }
      }
    },
    xAxis: {
      type: 'value',
      min: MAP_UTM.xMin,
      max: MAP_UTM.xMax,
      axisLine: { show: false },
      splitLine: { show: false },
      axisTick: { show: false },
      axisLabel: { show: false }
    },
    yAxis: {
      type: 'value',
      min: MAP_UTM.yMin,
      max: MAP_UTM.yMax,
      axisLine: { show: false },
      splitLine: { show: false },
      axisTick: { show: false },
      axisLabel: { show: false }
    },
    series: [
      ...robotSeries,
      {
        type: 'lines',
        coordinateSystem: 'cartesian2d',
        data: (mapData.value.links || []).map(link => ({
          coords: [
            [link.source[0], link.source[1]],
            [link.target[0], link.target[1]]
          ]
        })),
        lineStyle: {
          color: '#2196F3',
          width: 2,
          opacity: 0.8
        },
        zlevel: 1
      },
      {
        type: 'scatter',
        data: (mapData.value.nodes || []).map(node => [node.id[0], node.id[1]]),
        symbolSize: (value) => {
          return selectedNodes.value?.some(selected => 
            selected.id[0] === value[0] && selected.id[1] === value[1]
          ) ? 20 : 8
        },
        itemStyle: {
          color: (params) => {
            const node = mapData.value.nodes[params.dataIndex]
            return selectedNodes.value?.some(selected => 
              selected.id[0] === node.id[0] && selected.id[1] === node.id[1]
            ) ? '#ff4081' : '#007bff'
          }
        },
        label: {
          show: true,
          formatter: (params) => {
            const node = mapData.value.nodes[params.dataIndex]
            const index = selectedNodes.value?.findIndex(selected => 
              selected.id[0] === node.id[0] && selected.id[1] === node.id[1]
            )
            return index !== -1 ? (index + 1).toString() : ''
          },
          color: '#fff',
          fontSize: 12,
          fontWeight: 'bold',
          position: 'inside'
        },
        emphasis: {
          scale: 1.5,
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.3)'
          }
        },
        zlevel: 2
      }
    ]
  }
})

function updateChartSeries() {
  // Early return if required refs are not available
  if (!chartRef.value || !mapData.value) {
    console.warn('Chart reference or map data not available');
    return;
  }

  const seriesData = [];

  // Add lines series (paths between nodes)
  if (mapData.value.links && Array.isArray(mapData.value.links)) {
    seriesData.push({
      type: 'lines',
      coordinateSystem: 'cartesian2d',
      data: mapData.value.links.map(link => ({
        coords: [
          [link.source[0], link.source[1]],
          [link.target[0], link.target[1]]
        ]
      })),
      lineStyle: {
        color: '#2196F3',
        width: 2,
        opacity: 0.8
      },
      zlevel: 1
    });
  }

  // Add nodes series (waypoints)
  if (mapData.value.nodes && Array.isArray(mapData.value.nodes)) {
    seriesData.push({
      type: 'scatter',
      data: mapData.value.nodes.map(node => [node.id[0], node.id[1]]),
      symbolSize: (value) => {
        return selectedNodes.value?.some(sel => 
          sel.id[0] === value[0] && sel.id[1] === value[1]
        ) ? 20 : 8;
      },
      itemStyle: {
        color: (params) => {
          const node = mapData.value.nodes[params.dataIndex];
          return selectedNodes.value?.some(sel =>
            sel.id[0] === node.id[0] && sel.id[1] === node.id[1]
          ) ? '#ff4081' : '#007bff';
        }
      },
      label: {
        show: true,
        formatter: (params) => {
          const node = mapData.value.nodes[params.dataIndex];
          const index = selectedNodes.value?.findIndex(sel => 
            sel.id[0] === node.id[0] && sel.id[1] === node.id[1]
          );
          return index !== -1 ? (index + 1).toString() : '';
        },
        color: '#fff',
        fontSize: 12,
        fontWeight: 'bold',
        position: 'inside'
      },
      emphasis: {
        scale: 1.5,
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.3)'
        }
      },
      zlevel: 2
    });
  }

  // Add robot position series based on mode
  robotPositions.value?.forEach((position, robotSeq) => {
    if (position && 
        typeof position.x === 'number' && 
        typeof position.y === 'number' &&
        !isNaN(position.x) && 
        !isNaN(position.y)) {
      const isSelectedRobot = !props.isMonitoringMode && robotSeq === currentRobotSeq.value;
      
      seriesData.push({
        type: 'scatter',
        data: [[position.x, position.y]],
        symbolSize: 15,
        itemStyle: {
          color: isSelectedRobot ? '#ff0000' : robotColors[robotSeq % Object.keys(robotColors).length]
        },
        symbol: 'circle',
        zlevel: 3,
        tooltip: {
          formatter: () => {
            const robot = robotsStore.robots.find(r => r.seq === robotSeq);
            return `??: ${robot?.nickname || robot?.manufactureName || robotSeq}`;
          }
        }
      });
    }
  });

  // Safely update chart options
  try {
    chartRef.value.setOption({
      series: seriesData
    }, { 
      lazyUpdate: true,
      silent: true // Suppress unnecessary warnings
    });
  } catch (error) {
    console.error('Failed to update chart series:', error);
  }
}

// SSE ???
function setupSSE() {
  // ?? ????????
  if (robotPositions.value) {
    robotPositions.value.clear() // ?? ??? ?????????
  }
  if (eventSources) {
    eventSources.forEach(source => source.close())
    eventSources.clear()
  }
  
  // seq? 1??2?????????????SSE ???
  const newEventSources = new Map()
  
  const activeRobots = robotsStore.robots
    .filter(robot => (robot.seq === 1 || robot.seq === 2) && (robot?.isActive === true || robot?.IsActive === true));
  
  activeRobots.forEach(robot => {
    console.log(`Setting up SSE for robot ${robot.seq}`) // ?????
    const url = `/api/v1/robots/sse/${robot.seq}/down-utm`
    const eventSource = new EventSource(url)
    
    let lastUpdate = 0
    const updateInterval = 300

    eventSource.onmessage = (event) => {
      try {
        const now = Date.now()
        if (now - lastUpdate < updateInterval) return

        const data = JSON.parse(event.data)
        if (data && data.position && 
            typeof data.position.x === 'number' && 
            typeof data.position.y === 'number' &&
            !isNaN(data.position.x) && 
            !isNaN(data.position.y)) {
          robotPositions.value.set(robot.seq, {
            x: data.position.x,
            y: data.position.y
          })
          lastUpdate = now
        }
      } catch (error) {
        console.error(`SSE message parsing error (?? ${robot.seq}):`, error)
      }
    }

    eventSource.onerror = (error) => {
      console.error(`SSE ??? ??? (?? ${robot.seq}):`, error)
      eventSource.close()
      robotPositions.value.delete(robot.seq) // ??? ????? ?????????
    }

    newEventSources.set(robot.seq, eventSource)
  })

  return newEventSources
}

// ?? ??? ?????
async function handleNavigate() {
  try {
    await robotCommandsStore.navigateCommand(selectedNodes.value, currentRobotSeq.value)
    // ?? ??? ?????????? ????
    selectedNodes.value = []
    updateChartSeries()
    emit('selectedNodesChange', selectedNodes.value)
  } catch (error) {
    console.error('Navigation command failed:', error)
  }
}

async function handlePatrol() {
  try {
    await robotCommandsStore.patrolCommand(selectedNodes.value, currentRobotSeq.value)
    // ?? ??? ?????????? ????
    selectedNodes.value = []
    updateChartSeries()
    emit('selectedNodesChange', selectedNodes.value)
  } catch (error) {
    console.error('Patrol command failed:', error)
  }
}

async function resetSelection() {
  selectedNodes.value = await robotCommandsStore.resetSelectionCommand(currentRobotSeq.value)
  updateChartSeries()
}

async function handleTempStop() {
  await robotCommandsStore.tempStopCommand(currentRobotSeq.value)
}

async function handleResume() {
  await robotCommandsStore.resumeCommand(currentRobotSeq.value)
}

// ??? ??? ?????
function handleNodeClick(params) {
  // ????? ?????????? ??? ?????
  if (props.isMonitoringMode) return
  
  if (params.componentSubType === 'scatter') {
    const clickedNode = mapData.value.nodes[params.dataIndex]
    if (!clickedNode) return

    const index = selectedNodes.value.findIndex(n =>
      n.id[0] === clickedNode.id[0] && n.id[1] === clickedNode.id[1]
    )

    if (index === -1) {
      selectedNodes.value.push(clickedNode)
    } else {
      selectedNodes.value.splice(index, 1)
    }

    updateChartSeries()
    emit('selectedNodesChange', selectedNodes.value)
  }
}

// ??? ??? ?????
const handleNodeRemove = ({ node }) => {
  const index = selectedNodes.value.findIndex(n => 
    n.id[0].toFixed(2) === node.x && n.id[1].toFixed(2) === node.y
  )
  
  if (index !== -1) {
    selectedNodes.value = selectedNodes.value.filter((_, i) => i !== index)
    updateChartSeries()
    emit('selectedNodesChange', selectedNodes.value)
  }
}

// 배경 이미지를 UTM 좌표계에 정확히 배치 (convertToPixel 사용)
function updateBgImage() {
  if (!chartRef.value) return
  try {
    const tl = chartRef.value.convertToPixel(
      { xAxisIndex: 0, yAxisIndex: 0 },
      [MAP_UTM.xMin, MAP_UTM.yMax]   // 좌상단 (x최소, y최대)
    )
    const br = chartRef.value.convertToPixel(
      { xAxisIndex: 0, yAxisIndex: 0 },
      [MAP_UTM.xMax, MAP_UTM.yMin]   // 우하단 (x최대, y최소)
    )
    if (!tl || !br) return
    const w = br[0] - tl[0]
    const h = br[1] - tl[1]
    if (w <= 0 || h <= 0) return

    // 위치가 실질적으로 바뀌었을 때만 setOption (무한루프 방지)
    const pos = `${tl[0].toFixed(0)},${tl[1].toFixed(0)},${w.toFixed(0)},${h.toFixed(0)}`
    if (pos === _lastBgPos) return
    _lastBgPos = pos

    chartRef.value.setOption({
      graphic: [{
        type: 'image',
        id: 'bgMapFloor',
        z: -10,
        x: tl[0],
        y: tl[1],
        style: {
          image: '/images/map-floor.png',
          width: w,
          height: h,
          opacity: 0.75
        }
      }]
    })
  } catch (e) {
    console.warn('[RobotMap] bg image positioning error:', e)
  }
}

// ???????fetch
async function fetchMapData() {
  try {
    loading.value = true
    const response = await axios.get('/api/v1/map')
    mapData.value = { nodes: response.data.nodes, links: response.data.links }
    updateChartSeries()
  } catch (error) {
    console.error('????????? ???:', error)
  } finally {
    loading.value = false
  }
}

// Watchers
let eventSources = new Map()

// robotsStore.robots? ??? ??SSE ?????
// robots seq ??? ?? ?? SSE ??? (?? ?? ? ???? ??? ??)
watch(
  () => robotsStore.robots.map(r => r.seq).join(','),
  () => {
    eventSources.forEach(source => source.close())
    eventSources.clear()
    eventSources = setupSSE()
  }
)

// currentRobotSeq ???????????????????????
watch(() => currentRobotSeq.value, () => {
  updateChartSeries()
})

watch([() => robotPositions.value], () => {
  if (chartRef.value && mapData.value) {
    updateChartSeries()
  }
}, { deep: true })

watch(selectedNodes, () => {
  updateChartSeries()
})

// ?? ???? ??? ?? ?? ?? ??? (?? ??? ??)
watch(() => props.robot?.seq, (newSeq, oldSeq) => {
  if (newSeq && newSeq !== oldSeq) {
    selectedNodes.value = []
    updateChartSeries()
  }
})

// Lifecycle hooks
onMounted(() => {
  const resizeObserver = new ResizeObserver((entries) => {
    for (const entry of entries) {
      const { width, height } = entry.contentRect
      imageWidth.value = width * 0.9
      imageHeight.value = height * 0.95

      if (chartRef.value) {
        _lastBgPos = null   // 리사이즈 후 이미지 재배치 강제
        chartRef.value.resize()
      }
    }
  })

  if (containerRef.value) {
    resizeObserver.observe(containerRef.value)
  }

  fetchMapData()
  eventSources = setupSSE()
})

onUnmounted(() => {
  console.log('Cleaning up SSE connections...') // ?????
  eventSources.forEach(source => {
    source.close()
    console.log('Closed SSE connection') // ?????
  })
  eventSources.clear()
  robotPositions.value.clear() // ??? ????????
})

// ???????????????
defineExpose({
  handleNavigate,
  handlePatrol,
  resetSelection,
  handleTempStop,
  handleResume
})
</script>