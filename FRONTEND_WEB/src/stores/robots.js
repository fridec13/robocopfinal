import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useRobotsStore = defineStore('robots', () => {
  const robots = ref([])
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
  const selectedRobot = ref(savedRobot ? parseInt(savedRobot, 10) : 0)  // localStorage?êÏÑú Í∞Ä?∏Ïò® Î¨∏Ïûê?¥ÏùÑ parseIntÎ°?Î≥Ä??
  let pollingInterval = null
  const POLLING_INTERVAL = 500
 // localStorage?Ä ?∞Îèô?òÎäî ?¨Ïù¥?úÎ∞î ?ÅÌÉú
  const storedLeftState = localStorage.getItem("left-sidebar-collapsed");
  const leftSidebarCollapsed = ref(storedLeftState === "true");
  // App.vue???†Í? ?®Ïàò?Ä ?∞Îèô
  const updateSidebarStates = (left) => {
    leftSidebarCollapsed.value = left;
  };

  // Î°úÎ¥á Î¶¨Ïä§??Î∂àÎü¨?§Í∏∞
  const loadRobots = async () => {
    try {
      const res = await axios.get('/api/v1/robots/')
      if (res.data?.data && Array.isArray(res.data.data)) {
        robots.value = res.data.data.map(mapRobotData)
      } else {
        console.error('?àÏÉÅÏπ?Î™ªÌïú ?∞Ïù¥??Íµ¨Ï°∞:', res.data)
        robots.value = []
      }
    } catch (err) {
      console.error('Î°úÎ¥á ?∞Ïù¥??Î°úÎìú ?êÎü¨:', err)
      robots.value = []
    }
  }

  // ?πÏÜåÏº??∞Ïù¥?∞Ï? DB ?∞Ïù¥??Î≥ëÌï©
  const displayRobots = computed(() => robots.value)

  // API ?¥ÎßÅ Í¥Ä??
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
        } else {
          console.error('?àÏÉÅÏπ?Î™ªÌïú ?∞Ïù¥??Íµ¨Ï°∞:', res.data)
        }
      } catch (error) {
        console.error('?¥ÎßÅ ?êÎü¨:', error)
      }
    }, POLLING_INTERVAL)
  }

  const stopPolling = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval)
      pollingInterval = null
    }
  }  

    // Í≥µÌÜµ Îß§Ìïë ?®Ïàò Ï∂îÍ?
    const mapRobotData = (robot) => ({
      seq: robot.seq,
      manufactureName: robot.manufactureName,
      nickname: robot.nickname || '',
      sensorName: robot.sensorName || '',
      ipAddress: robot.ipAddress || '?????ÜÏùå',
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

  // Î°úÎ¥á ?âÎÑ§???§Ï†ï
  const openNicknameModal = (robot) => {
    selectedRobotForNickname.value = robot
    showNicknameModal.value = true
  }

  const closeNicknameModal = () => {
    showNicknameModal.value = false
    selectedRobotForNickname.value = null
  }

  // Î°úÎ¥á ?†ÌÉù Ï≤òÎ¶¨ ??Î°úÏª¨ ?§ÌÜ†Î¶¨Ï? ?Ä??
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
          nickname: registeredRobot.nickname,   // Ï£ºÏùò: robot -> registeredRobot
          ipAddress: registeredRobot.ipAddress,
          sensorName: registeredRobot.sensorName || '',
          status: registeredRobot.status || 'waiting',
          battery: registeredRobot.battery?.level || 100,
          isCharging: registeredRobot.battery?.isCharging || false,
          networkStatus: registeredRobot.networkStatus || 'connected',
          networkHealth: registeredRobot.networkHealth || 100,
          position: registeredRobot.position
            ? `x: ${registeredRobot.position.x}, y: ${registeredRobot.position.y}`
            : '?????ÜÏùå',
          orientation: registeredRobot.position?.orientation || '?????ÜÏùå',
          motion: registeredRobot.motion 
          ? `kph: ${registeredRobot.motion.kph}, mps: ${registeredRobot.motion.mps}`
          : '?????ÜÏùå',
          cpuTemp: registeredRobot.cpuTemp || 0.0,
          waypoints : registeredRobot.waypoints || [],
          imageUrl: registeredRobot.image?.url || '',
          startAt: registeredRobot.startAt || '?????ÜÏùå',
          lastActive: registeredRobot.lastActive || '?????ÜÏùå',
          isActive: registeredRobot.IsActive || false
        })

        closeModal()
        alert('Î°úÎ¥á ?±Î°ù ?±Í≥µ')
      })
      .catch((err) => {
        console.error('Î°úÎ¥á ?±Î°ù ?§Ìå®:', err)
        alert('Î°úÎ¥á ?±Î°ù???§Ìå®?àÏäµ?àÎã§.')
      })
  }

  // Î°úÎ¥á Í¥ÄÎ¶?Î™®Îã¨ ?¥Í∏∞/?´Í∏∞
  const openRobotManagementModal = () => { showRobotManagementModal.value = true }
  const closeRobotManagementModal = () => { showRobotManagementModal.value = false }

  // Î°úÎ¥á ?±Î°ù Î™®Îã¨ ?¥Í∏∞ (Î°úÎ¥á Í¥ÄÎ¶?Î™®Îã¨???´Í≥† ?¥Í∏∞)
  const openAddRobotModal = () => {
    showRobotManagementModal.value = false
    showModal.value = true
  }

  // Î°úÎ¥á ?±Î°ù Î™®Îã¨ ?´Í∏∞
  const closeModal = () => {
    showModal.value = false
    newRobot.value = {
      nickname: '',
      ipAddress: ''
    }
  }

const updateRobotPosition = (seq, position) => {
  const robotIndex = robots.value.findIndex(r => r.seq === seq);
  if (robotIndex !== -1) {
    robots.value[robotIndex] = {
      ...robots.value[robotIndex],
      position: {
        x: position.x,
        y: position.y,
      }
    };
  }
}

const updateRobotStatus = (seq, statusData) => {
  const robot = robots.value.find(r => r.seq === seq);
  if (robot) {
    Object.assign(robot, statusData);
  }
}

  return {
    robots,
    showModal,
    showRobotManagementModal,
    newRobot,
    // ?´ÏûêÎ°?Í¥ÄÎ¶¨Îêò??selectedRobot
    selectedRobot,
    showNicknameModal,
    selectedRobotForNickname,
    robotNicknames,
    displayRobots,
    leftSidebarCollapsed,

    // methods
    updateRobotPosition,
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
    updateRobotStatus
  }
})
