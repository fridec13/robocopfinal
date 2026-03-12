import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useRobotsStore = defineStore('robots', () => {
  const robots = ref([])
  // SSE? ??? ??? ??? (??? ?? ????? ??)
  const liveStatus = ref({})  // { [seq]: { status, battery, networkHealth, cpuTemp, startAt, isActive, position } }
  const statusSSEs = {}       // ?? ?? SSE ?? ??
  const showRobotManagementModal = ref(false)
  const showNicknameModal = ref(false)
  const selectedRobotForNickname = ref(null)
  const robotNicknames = ref(JSON.parse(localStorage.getItem('robot_nicknames')) || {})
  const showModal = ref(false)
  const newRobot = ref({
    nickname: '',
    ipAddress: '',
  })
  const savedRobot = localStorage.getItem('selectedRobot')
  const selectedRobot = ref(savedRobot ? parseInt(savedRobot, 10) : 0)  // localStorage??? ???? ????? parseInt?????
  let pollingInterval = null
  const POLLING_INTERVAL = 500
 // localStorage?? ?????? ?????? ???
  const storedLeftState = localStorage.getItem("left-sidebar-collapsed");
  const leftSidebarCollapsed = ref(storedLeftState === "true");
  // App.vue?????? ????? ???
  const updateSidebarStates = (left) => {
    leftSidebarCollapsed.value = left;
  };

  // ?? ?????????
  const loadRobots = async () => {
    try {
      const res = await axios.get('/api/v1/robots/')
      if (res.data?.data && Array.isArray(res.data.data)) {
        robots.value = res.data.data.map(mapRobotData)
      } else {
        console.error('??????? ???????:', res.data)
        robots.value = []
      }
    } catch (err) {
      console.error('?? ??????? ???:', err)
      robots.value = []
    }
  }

  // ???????????? DB ???????
  // DB ??? + SSE ??? ??? ?? (SSE ??)
  const displayRobots = computed(() =>
    robots.value.map(robot => ({
      ...robot,
      ...(liveStatus.value[robot.seq] || {})
    }))
  )

  // API ??? ???
  const startPolling = () => {
    if (pollingInterval) {
      stopPolling()
    }

    loadRobots()

    pollingInterval = setInterval(async () => {
      try {
        const res = await axios.get('/api/v1/robots/')
        if (res.data?.data && Array.isArray(res.data.data)) {
          robots.value = res.data.data.map(mapRobotData)
          // ?? ?? ?? SSE ?? ??
          robots.value.forEach(r => { if (r.isActive) setupGlobalStatusSSE(r.seq) })
        }
      } catch (error) {
        console.error('?? ??:', error)
      }
    }, POLLING_INTERVAL)
  }

  const stopPolling = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval)
      pollingInterval = null
    }
  }  

    // ?? ?? ??? ???
    const mapRobotData = (robot) => ({
      seq: robot.seq,
      manufactureName: robot.manufactureName,
      nickname: robot.nickname || '',
      sensorName: robot.sensorName || '',
      ipAddress: robot.ipAddress || '???????',
      networkStatus: robot.networkStatus || 'disconnected',
      status: robot.status || 'waiting',
      networkHealth: robot.networkHealth || 100,
      position: robot.position || { x: 0, y: 0, z: 0 },
      orientation: robot.orientation || 0,
      motion: robot.motion || { kph: 0, mps: 0 },
      battery: {
        level: robot.battery?.level || 100,
        isCharging: robot.battery?.isCharging || false,
        lastCharged: robot.battery?.lastCharged || null
      },
      cpuTemp: robot.cpuTemp || 0,
      waypoints: robot.waypoints || [],
      startAt: robot.startAt || new Date().toISOString(),
      isActive: robot.IsActive ?? true,
      isDeleted: robot.IsDeleted || false,
      lastActive: robot.lastActive || new Date().toISOString(),
      createdAt: robot.createdAt || new Date().toISOString(),
      updatedAt: robot.updatedAt || new Date().toISOString()
    })

  // ?? ????????
  const openNicknameModal = (robot) => {
    selectedRobotForNickname.value = robot
    showNicknameModal.value = true
  }

  const closeNicknameModal = () => {
    showNicknameModal.value = false
    selectedRobotForNickname.value = null
  }

  // ?? ??? ?? ???? ?????? ????
  const handleRobotSelection = () => {
    if (selectedRobot.value !== 0) {
      localStorage.setItem('selectedRobot', String(selectedRobot.value))
    } else {
      localStorage.removeItem('selectedRobot')
    }
  }

  const handleAddRobot = () => {
    const formData = new FormData()
    formData.append('nickname', newRobot.value.nickname)
    formData.append('ipAddress', newRobot.value.ipAddress)

    axios.post('/api/v1/robots/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
      .then((response) => {
        const registeredRobot = response.data.data
        robots.value.push({
          seq: registeredRobot.seq,
          manufactureName: registeredRobot.manufactureName,
          nickname: registeredRobot.nickname,   // ??: robot -> registeredRobot
          ipAddress: registeredRobot.ipAddress,
          sensorName: registeredRobot.sensorName || '',
          status: registeredRobot.status || 'waiting',
          battery: registeredRobot.battery?.level || 100,
          isCharging: registeredRobot.battery?.isCharging || false,
          networkStatus: registeredRobot.networkStatus || 'connected',
          networkHealth: registeredRobot.networkHealth || 100,
          position: registeredRobot.position
            ? `x: ${registeredRobot.position.x}, y: ${registeredRobot.position.y}`
            : '???????',
          orientation: registeredRobot.position?.orientation || '???????',
          motion: registeredRobot.motion 
          ? `kph: ${registeredRobot.motion.kph}, mps: ${registeredRobot.motion.mps}`
          : '???????',
          cpuTemp: registeredRobot.cpuTemp || 0.0,
          waypoints : registeredRobot.waypoints || [],
          imageUrl: registeredRobot.image?.url || '',
          startAt: registeredRobot.startAt || '???????',
          lastActive: registeredRobot.lastActive || '???????',
          isActive: registeredRobot.IsActive || false
        })

        closeModal()
        alert('?? ??? ???')
      })
      .catch((err) => {
        console.error('?? ??? ???:', err)
        alert('?? ??????????????.')
      })
  }

  // ?? ????? ???/???
  const openRobotManagementModal = () => { showRobotManagementModal.value = true }
  const closeRobotManagementModal = () => { showRobotManagementModal.value = false }

  // ?? ??? ?? ??? (?? ?????????? ???)
  const openAddRobotModal = () => {
    showRobotManagementModal.value = false
    showModal.value = true
  }

  // ?? ??? ?? ???
  const closeModal = () => {
    showModal.value = false
    newRobot.value = {
      nickname: '',
      ipAddress: ''
    }
  }

const updateRobotPosition = (seq, position) => {
  liveStatus.value = {
    ...liveStatus.value,
    [seq]: { ...(liveStatus.value[seq] || {}), position: { x: position.x, y: position.y } }
  }
}

const updateRobotStatus = (seq, statusData) => {
  liveStatus.value = {
    ...liveStatus.value,
    [seq]: { ...(liveStatus.value[seq] || {}), ...statusData }
  }
}

// ?? ?? SSE - ??/?? ?? ?????? ??? ??
const setupGlobalStatusSSE = (seq) => {
  if (statusSSEs[seq]) return
  const es = new EventSource(`/api/v1/robots/sse/${seq}/status`)
  es.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.status && Object.keys(data.status).length > 0) {
        updateRobotStatus(seq, {
          status:        data.status.status,
          battery:       data.status.battery,
          networkHealth: data.status.networkHealth,
          cpuTemp:       data.status.cpuTemp,
          startAt:       data.status.startAt,
          isActive:      data.status.isActive,
        })
      }
    } catch {}
  }
  es.onerror = () => {
    es.close()
    delete statusSSEs[seq]
  }
  statusSSEs[seq] = es
}

  return {
    robots,
    showModal,
    showRobotManagementModal,
    newRobot,
    // ??????????selectedRobot
    selectedRobot,
    showNicknameModal,
    selectedRobotForNickname,
    robotNicknames,
    displayRobots,
    leftSidebarCollapsed,

    // methods
    updateRobotPosition,
    updateRobotStatus,
    setupGlobalStatusSSE,
    updateSidebarStates,
    openNicknameModal,
    closeNicknameModal,
    openRobotManagementModal,
    closeRobotManagementModal,
    loadRobots,
    openAddRobotModal,
    handleRobotSelection,
    closeModal,
    handleAddRobot,
    startPolling,
    stopPolling,
  }
})
