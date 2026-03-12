<template>
  <div class="h-full overflow-y-auto bg-gray-100 p-5" @keydown.prevent="onKey" tabindex="0" ref="pageRef">
    <div class="border-b pb-2 mb-4">
      <h2 class="text-2xl font-bold text-gray-800">{{ '\ub85c\ubd07 \uc81c\uc5b4' }}</h2>
    </div>

    <!-- 로봇 선택 -->
    <div class="bg-white rounded-lg shadow-md p-4 mb-4 flex items-center gap-4">
      <label class="text-sm font-semibold text-gray-700">{{ '\uc81c\uc5b4\ud560 \ub85c\ubd07:' }}</label>
      <select v-model="selectedSeq" class="p-2 border rounded-lg text-sm">
        <option v-for="robot in robots" :key="robot.seq" :value="robot.seq">
          {{ robot.nickname || robot.name }} (seq={{ robot.seq }})
        </option>
      </select>
      <span
        class="px-2 py-1 rounded text-xs font-bold"
        :class="isManualMode ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'"
      >
        {{ isManualMode ? '\uc218\ub3d9 \ubaa8\ub4dc' : '\ub300\uae30 \ubaa8\ub4dc' }}
      </span>
      <button
        v-if="!isManualMode"
        @click="enterManual"
        class="px-3 py-1.5 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
      >{{ '\uc218\ub3d9 \ubaa8\ub4dc \uc9c4\uc785' }}</button>
      <button
        v-else
        @click="exitManual"
        class="px-3 py-1.5 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
      >{{ '\uc9c4\uc785 \ud574\uc81c' }}</button>
    </div>

    <div class="bg-white rounded-lg shadow-md p-6">
      <h3 class="text-lg font-semibold mb-1">{{ '\uc218\ub3d9 \uc81c\uc5b4' }}</h3>
      <p class="text-sm text-gray-500 mb-5">
        {{ '\ud654\uc0b4\ud45c \ud0a4 \ub610\ub294 WASD \ud0a4\ub85c \ub85c\ubd07\uc744 \uc81c\uc5b4\ud569\ub2c8\ub2e4. \uc218\ub3d9 \ubaa8\ub4dc \uc9c4\uc785 \ud6c4 \uc0ac\uc6a9\ud558\uc138\uc694.' }}
      </p>

      <!-- 방향 패드 -->
      <div class="grid grid-cols-3 gap-2 w-44 mx-auto select-none">
        <div></div>
        <button
          @mousedown="startCmd('forward')" @mouseup="stopCmd" @mouseleave="stopCmd"
          @touchstart.prevent="startCmd('forward')" @touchend="stopCmd"
          :class="['p-3 rounded text-center font-bold text-lg transition-colors',
            activeDir === 'forward' ? 'bg-blue-400 text-white' : 'bg-gray-200 hover:bg-gray-300']"
        >&#8593;</button>
        <div></div>

        <button
          @mousedown="startCmd('left')" @mouseup="stopCmd" @mouseleave="stopCmd"
          @touchstart.prevent="startCmd('left')" @touchend="stopCmd"
          :class="['p-3 rounded text-center font-bold text-lg transition-colors',
            activeDir === 'left' ? 'bg-blue-400 text-white' : 'bg-gray-200 hover:bg-gray-300']"
        >&#8592;</button>
        <button
          @click="sendCmd('stop')"
          class="p-3 bg-red-200 rounded hover:bg-red-300 text-center font-bold text-red-700"
        >{{ '\uc815\uc9c0' }}</button>
        <button
          @mousedown="startCmd('right')" @mouseup="stopCmd" @mouseleave="stopCmd"
          @touchstart.prevent="startCmd('right')" @touchend="stopCmd"
          :class="['p-3 rounded text-center font-bold text-lg transition-colors',
            activeDir === 'right' ? 'bg-blue-400 text-white' : 'bg-gray-200 hover:bg-gray-300']"
        >&#8594;</button>

        <div></div>
        <button
          @mousedown="startCmd('backward')" @mouseup="stopCmd" @mouseleave="stopCmd"
          @touchstart.prevent="startCmd('backward')" @touchend="stopCmd"
          :class="['p-3 rounded text-center font-bold text-lg transition-colors',
            activeDir === 'backward' ? 'bg-blue-400 text-white' : 'bg-gray-200 hover:bg-gray-300']"
        >&#8595;</button>
        <div></div>
      </div>

      <!-- 속도 슬라이더 -->
      <div class="mt-6 max-w-xs mx-auto">
        <label class="text-sm font-semibold text-gray-700">
          {{ '\uc18d\ub3c4:' }} {{ speed.toFixed(1) }}
        </label>
        <input type="range" v-model.number="speed" min="0.1" max="1.0" step="0.1" class="w-full mt-1" />
      </div>

      <!-- 키 안내 -->
      <div class="mt-5 text-xs text-gray-400 text-center space-y-1">
        <p>{{ '\ud654\uc0b4\ud45c \ud0a4 \ub610\ub294 W\u00b7A\u00b7S\u00b7D \ub85c \uc774\ub3d9 / \uc2a4\ud398\uc774\uc2a4\ubc14 \ub85c \uc815\uc9c0' }}</p>
        <p v-if="lastCmd" class="text-blue-500 font-medium">
          {{ '\ub9c8\uc9c0\ub9c9 \uba85\ub839:' }} {{ lastCmd }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useRobotsStore } from '@/stores/robots'
import { useRobotCommandsStore } from '@/stores/robotCommands'

const robotsStore = useRobotsStore()
const robotCommandsStore = useRobotCommandsStore()

const pageRef = ref(null)
const speed = ref(0.5)
const activeDir = ref(null)
const lastCmd = ref('')
const isManualMode = ref(false)
const selectedSeq = ref(null)

const robots = computed(() => robotsStore.robots)

// 로봇 목록이 로드되면 첫 번째 로봇 자동 선택
onMounted(async () => {
  await robotsStore.loadRobots()
  if (robots.value.length > 0 && !selectedSeq.value) {
    selectedSeq.value = robots.value[0].seq
  }
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
  pageRef.value?.focus()
})

onUnmounted(async () => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
  // 페이지 나갈 때 수동 모드였으면 대기 모드로 복귀
  if (isManualMode.value && selectedSeq.value) {
    await sendCmd('stop')
    await robotCommandsStore.waitingCommand?.(selectedSeq.value)
  }
})

const enterManual = async () => {
  if (!selectedSeq.value) return
  try {
    await axios.post(`/api/v1/ros/${selectedSeq.value}/call-service/manual`, null, {
      headers: { Authorization: `Bearer ${localStorage.getItem('accessToken')}` }
    })
    isManualMode.value = true
  } catch (e) {
    console.error('\uc218\ub3d9 \ubaa8\ub4dc \uc9c4\uc785 \uc2e4\ud328:', e)
  }
}

const exitManual = async () => {
  if (!selectedSeq.value) return
  await sendCmd('stop')
  try {
    await axios.post(`/api/v1/ros/${selectedSeq.value}/call-service/waiting`, null, {
      headers: { Authorization: `Bearer ${localStorage.getItem('accessToken')}` }
    })
    isManualMode.value = false
  } catch (e) {
    console.error('\uc218\ub3d9 \ubaa8\ub4dc \ud574\uc81c \uc2e4\ud328:', e)
  }
}

let cmdInterval = null

const sendCmd = async (dir) => {
  if (!selectedSeq.value) return
  try {
    await axios.post(
      `/api/v1/ros/${selectedSeq.value}/cmd_vel`,
      null,
      {
        params: { direction: dir.toUpperCase() },
        headers: { Authorization: `Bearer ${localStorage.getItem('accessToken')}` }
      }
    )
    lastCmd.value = dir
  } catch (e) {
    console.error('\uba85\ub839 \uc804\uc1a1 \uc2e4\ud328:', e)
  }
}

// 버튼 누르고 있는 동안 반복 전송
const startCmd = (dir) => {
  if (!isManualMode.value) return
  activeDir.value = dir
  sendCmd(dir)
  cmdInterval = setInterval(() => sendCmd(dir), 150)
}

const stopCmd = () => {
  if (cmdInterval) { clearInterval(cmdInterval); cmdInterval = null }
  activeDir.value = null
  sendCmd('stop')
}

// 키보드 매핑
const keyMap = {
  ArrowUp: 'forward', w: 'forward', W: 'forward',
  ArrowDown: 'backward', s: 'backward', S: 'backward',
  ArrowLeft: 'left', a: 'left', A: 'left',
  ArrowRight: 'right', d: 'right', D: 'right',
  ' ': 'stop',
}

const pressedKeys = new Set()

const onKeyDown = (e) => {
  if (!isManualMode.value) return
  // 입력 필드에 포커스 중이면 무시
  if (['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return
  const dir = keyMap[e.key]
  if (!dir) return
  e.preventDefault()
  if (pressedKeys.has(e.key)) return  // 키 반복 방지 (자체 interval 사용)
  pressedKeys.add(e.key)
  if (dir === 'stop') {
    sendCmd('stop')
    activeDir.value = null
  } else {
    activeDir.value = dir
    sendCmd(dir)
    cmdInterval = setInterval(() => sendCmd(dir), 150)
  }
}

const onKeyUp = (e) => {
  pressedKeys.delete(e.key)
  const dir = keyMap[e.key]
  if (!dir || dir === 'stop') return
  if (activeDir.value === dir) {
    if (cmdInterval) { clearInterval(cmdInterval); cmdInterval = null }
    activeDir.value = null
    sendCmd('stop')
  }
}

// 템플릿의 @keydown (div 포커스용 폴백)
const onKey = (e) => { /* window 리스너가 처리 */ }
</script>
