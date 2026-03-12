<template>
  <div class="h-full flex flex-col overflow-hidden bg-gray-100 p-4 gap-3">

    <!-- 상단 헤더 (로봇 선택 + 모드 토글) -->
    <div class="bg-white rounded-lg shadow-sm px-4 py-3 flex flex-wrap items-center gap-3">
      <h2 class="text-lg font-bold text-gray-800 mr-2">{{ '\ub85c\ubd07 \uc81c\uc5b4' }}</h2>

      <select v-model="selectedSeq" class="p-1.5 border rounded text-sm">
        <option v-for="robot in robots" :key="robot.seq" :value="robot.seq">
          {{ robot.nickname || robot.name }} (seq={{ robot.seq }})
        </option>
      </select>

      <span
        class="px-2 py-0.5 rounded text-xs font-bold"
        :class="isManualMode ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'"
      >
        {{ isManualMode ? '\ud604\uc7ac: \uc218\ub3d9 \ubaa8\ub4dc' : '\ud604\uc7ac: \ub300\uae30 \ubaa8\ub4dc' }}
      </span>

      <button
        v-if="!isManualMode"
        @click="enterManual"
        class="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 font-medium"
      >{{ '\uc218\ub3d9 \ubaa8\ub4dc \uc9c4\uc785' }}</button>
      <button
        v-else
        @click="exitManual"
        class="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600 font-medium"
      >{{ '\ubaa8\ub4dc \ud574\uc81c' }}</button>

      <span v-if="lastCmd" class="ml-auto text-xs text-blue-500 font-medium">
        {{ '\ub9c8\uc9c0\ub9c9 \uba85\ub839:' }} {{ lastCmd.toUpperCase() }}
      </span>
    </div>

    <!-- 메인 영역: 좌측 카메라+라이다 / 우측 조작패드 -->
    <div class="flex-1 flex gap-3 min-h-0">

      <!-- 좌측 — 전방 카메라 + 라이다 -->
      <div class="flex-1 min-w-0 flex flex-col gap-3 min-h-0">

        <!-- 전방 카메라 -->
        <div class="flex-[3] min-h-0 bg-black rounded-lg overflow-hidden flex flex-col">
          <div class="px-3 py-1.5 bg-gray-900 flex items-center gap-2">
            <span class="w-2 h-2 rounded-full" :class="isManualMode ? 'bg-green-400 animate-pulse' : 'bg-gray-500'"></span>
            <span class="text-xs text-gray-300 font-medium">
              {{ '\uc804\ubc29 \uce74\uba54\ub77c' }} — seq {{ selectedSeq }}
            </span>
          </div>
          <div class="flex-1 min-h-0">
            <Cctv
              v-if="selectedSeq"
              :robotSeq="selectedSeq"
              cameraType="front"
              class="w-full h-full"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-gray-500 text-sm">
              {{ '\ub85c\ubd07\uc744 \uc120\ud0dd\ud558\uc138\uc694' }}
            </div>
          </div>
        </div>

        <!-- 라이다 -->
        <div class="flex-[2] min-h-0 bg-gray-900 rounded-lg overflow-hidden flex flex-col">
          <div class="px-3 py-1.5 bg-gray-800 flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
            <span class="text-xs text-gray-300 font-medium">
              {{ '\ub77c\uc774\ub2e4' }} — seq {{ selectedSeq }}
            </span>
          </div>
          <div class="flex-1 min-h-0">
            <LidarViewer
              v-if="selectedSeq"
              :robotSeq="selectedSeq"
              class="w-full h-full"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-gray-500 text-sm">
              {{ '\ub85c\ubd07\uc744 \uc120\ud0dd\ud558\uc138\uc694' }}
            </div>
          </div>
        </div>

      </div>

      <!-- 우측 — 조작패드 -->
      <div class="w-56 flex-shrink-0 flex flex-col gap-3">

        <!-- 방향 패드 -->
        <div class="bg-white rounded-lg shadow-sm p-4 flex flex-col items-center gap-2">
          <p class="text-xs text-gray-500 mb-1">{{ '\ud654\uc0b4\ud45c \ud0a4 \ub610\ub294 WASD' }}</p>

          <div class="grid grid-cols-3 gap-1.5 w-36 select-none">
            <div></div>
            <button
              @mousedown="startCmd('up')" @mouseup="stopCmd" @mouseleave="stopCmd"
              @touchstart.prevent="startCmd('up')" @touchend="stopCmd"
              :class="btnClass('up')"
            >&#8593;</button>
            <div></div>

            <button
              @mousedown="startCmd('left')" @mouseup="stopCmd" @mouseleave="stopCmd"
              @touchstart.prevent="startCmd('left')" @touchend="stopCmd"
              :class="btnClass('left')"
            >&#8592;</button>
            <button
              @click="sendCmd('space')"
              class="p-3 rounded text-center font-bold text-sm bg-red-100 hover:bg-red-200 text-red-600 transition-colors"
            >{{ '\uc815\uc9c0' }}</button>
            <button
              @mousedown="startCmd('right')" @mouseup="stopCmd" @mouseleave="stopCmd"
              @touchstart.prevent="startCmd('right')" @touchend="stopCmd"
              :class="btnClass('right')"
            >&#8594;</button>

            <div></div>
            <button
              @mousedown="startCmd('down')" @mouseup="stopCmd" @mouseleave="stopCmd"
              @touchstart.prevent="startCmd('down')" @touchend="stopCmd"
              :class="btnClass('down')"
            >&#8595;</button>
            <div></div>
          </div>
        </div>

        <!-- 속도 슬라이더 -->
        <div class="bg-white rounded-lg shadow-sm p-4">
          <label class="text-xs font-semibold text-gray-600">
            {{ '\uc18d\ub3c4' }}: {{ speed.toFixed(1) }}
          </label>
          <input
            type="range" v-model.number="speed"
            min="0.1" max="1.0" step="0.1"
            class="w-full mt-1.5"
          />
          <div class="flex justify-between text-xs text-gray-400 mt-0.5">
            <span>0.1</span><span>1.0</span>
          </div>
        </div>

        <!-- 키 안내 -->
        <div class="bg-white rounded-lg shadow-sm p-3 text-xs text-gray-500 space-y-1">
          <p class="font-semibold text-gray-600">{{ '\ub2e8\ucda1\ud0a4' }}</p>
          <p>&#8593; / W — {{ '\uc804\uc9c4' }}</p>
          <p>&#8595; / S — {{ '\ud6c4\uc9c4' }}</p>
          <p>&#8592; / A — {{ '\uc88c\ud68c\uc804' }}</p>
          <p>&#8594; / D — {{ '\uc6b0\ud68c\uc804' }}</p>
          <p>Space — {{ '\uc815\uc9c0' }}</p>
          <p class="pt-1 text-orange-500">{{ '\uc218\ub3d9 \ubaa8\ub4dc \uc9c4\uc785 \ud6c4 \ud65c\uc131\ud654' }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useRobotsStore } from '@/stores/robots'
import Cctv from '@/components/camera/Cctv.vue'
import LidarViewer from '@/components/detail/LidarViewer.vue'

const robotsStore = useRobotsStore()

const speed = ref(0.5)
const activeDir = ref(null)
const lastCmd = ref('')
const isManualMode = ref(false)
const selectedSeq = ref(null)

const robots = computed(() => robotsStore.robots)

onMounted(async () => {
  await robotsStore.loadRobots()
  if (robots.value.length > 0 && !selectedSeq.value) {
    selectedSeq.value = robots.value[0].seq
  }
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
})

onUnmounted(async () => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
  if (isManualMode.value && selectedSeq.value) {
    await sendCmd('space')
    await callService('waiting')
  }
})

const authHeader = () => ({
  Authorization: `Bearer ${localStorage.getItem('accessToken')}`
})

const callService = async (name) => {
  await axios.post(`/api/v1/${selectedSeq.value}/call-service/${name}`, null, {
    headers: authHeader()
  })
}

const enterManual = async () => {
  if (!selectedSeq.value) return
  try {
    await callService('manual')
    isManualMode.value = true
  } catch (e) {
    console.error('\uc218\ub3d9 \ubaa8\ub4dc \uc2e4\ud328:', e)
  }
}

const exitManual = async () => {
  if (!selectedSeq.value) return
  await sendCmd('space')
  try {
    await callService('waiting')
    isManualMode.value = false
  } catch (e) {
    console.error('\ubaa8\ub4dc \ud574\uc81c \uc2e4\ud328:', e)
  }
}

let cmdInterval = null

const sendCmd = async (dir) => {
  if (!selectedSeq.value) return
  try {
    await axios.post(`/api/v1/${selectedSeq.value}/cmd_vel`, null, {
      params: { direction: dir.toUpperCase() },
      headers: authHeader()
    })
    lastCmd.value = dir
  } catch (e) {
    console.error('\uba85\ub839 \uc2e4\ud328:', e)
  }
}

const startCmd = (dir) => {
  if (!isManualMode.value) return
  activeDir.value = dir
  sendCmd(dir)
  if (cmdInterval) clearInterval(cmdInterval)
  cmdInterval = setInterval(() => sendCmd(dir), 150)
}

const stopCmd = () => {
  if (cmdInterval) { clearInterval(cmdInterval); cmdInterval = null }
  activeDir.value = null
  sendCmd('space')
}

const btnClass = (dir) => [
  'p-3 rounded text-center font-bold text-lg transition-colors',
  activeDir.value === dir
    ? 'bg-blue-400 text-white scale-95'
    : isManualMode.value
      ? 'bg-gray-200 hover:bg-blue-100 cursor-pointer'
      : 'bg-gray-100 text-gray-300 cursor-not-allowed'
]

// middle_teleop_node.cpp 기대값: UP / DOWN / LEFT / RIGHT / SPACE
const keyMap = {
  ArrowUp: 'up',    w: 'up',    W: 'up',
  ArrowDown: 'down', s: 'down',  S: 'down',
  ArrowLeft: 'left', a: 'left',  A: 'left',
  ArrowRight: 'right', d: 'right', D: 'right',
  ' ': 'space',
}

const pressedKeys = new Set()

const onKeyDown = (e) => {
  if (!isManualMode.value) return
  if (['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return
  const dir = keyMap[e.key]
  if (!dir) return
  e.preventDefault()
  if (dir === 'space') {
    sendCmd('space')
    activeDir.value = null
    return
  }
  if (pressedKeys.has(e.key)) return
  pressedKeys.add(e.key)
  activeDir.value = dir
  sendCmd(dir)
  if (cmdInterval) clearInterval(cmdInterval)
  cmdInterval = setInterval(() => sendCmd(dir), 150)
}

const onKeyUp = (e) => {
  pressedKeys.delete(e.key)
  const dir = keyMap[e.key]
  if (!dir || dir === 'space') return
  if (activeDir.value === dir) {
    if (cmdInterval) { clearInterval(cmdInterval); cmdInterval = null }
    activeDir.value = null
    sendCmd('space')
  }
}
</script>
