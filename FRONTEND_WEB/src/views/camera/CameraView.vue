<template>
  <div class="h-full flex flex-col bg-gray-100 p-4 gap-3 overflow-hidden">

    <!-- 헤더 + 컨트롤 -->
    <div class="flex-shrink-0 bg-white rounded-lg shadow-sm px-4 py-3 flex flex-wrap items-center gap-3">
      <h2 class="text-lg font-bold text-gray-800 mr-2">CCTV {{ '\uce74\uba54\ub77c' }}</h2>

      <!-- 로봇 선택 -->
      <div class="flex items-center gap-2">
        <label class="text-sm font-semibold text-gray-600">{{ '\ub85c\ubd07:' }}</label>
        <select v-model="selectedSeq" class="border border-gray-300 rounded px-2 py-1 text-sm">
          <option v-for="robot in robots" :key="robot.seq" :value="robot.seq">
            {{ robot.nickname || robot.name }} (seq={{ robot.seq }})
          </option>
        </select>
      </div>

      <!-- 화면 모드 -->
      <div class="flex items-center gap-2">
        <label class="text-sm font-semibold text-gray-600">{{ '\ud654\uba74 \ubaa8\ub4dc:' }}</label>
        <select v-model="viewMode" class="border border-gray-300 rounded px-2 py-1 text-sm">
          <option value="both">{{ '\uc591\ubc29\ud5a5' }}</option>
          <option value="front">{{ '\uc804\ubc29\ub9cc' }}</option>
          <option value="rear">{{ '\ud6c4\ubc29\ub9cc' }}</option>
        </select>
      </div>
    </div>

    <!-- 카메라 피드 -->
    <div
      class="flex-1 min-h-0 grid gap-3"
      :class="viewMode === 'both' ? 'grid-cols-2' : 'grid-cols-1'"
    >
      <div v-if="viewMode !== 'rear'" class="bg-white rounded-lg shadow-sm overflow-hidden">
        <Cctv :robot-seq="selectedSeq" camera-type="front" class="h-full" />
      </div>
      <div v-if="viewMode !== 'front'" class="bg-white rounded-lg shadow-sm overflow-hidden">
        <Cctv :robot-seq="selectedSeq" camera-type="rear" class="h-full" />
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import Cctv from '@/components/camera/Cctv.vue'
import { useRobotsStore } from '@/stores/robots'

const robotsStore = useRobotsStore()
const viewMode = ref('both')
const selectedSeq = ref(null)

const robots = computed(() => robotsStore.robots)

onMounted(async () => {
  await robotsStore.loadRobots()
  // 사이드바 선택 값이 있으면 유지, 없으면 첫 번째 로봇
  selectedSeq.value = robotsStore.selectedRobot || (robots.value[0]?.seq ?? null)
})

// 드롭박스에서 선택 바꾸면 스토어도 동기화
watch(selectedSeq, (seq) => {
  if (seq) {
    robotsStore.selectedRobot = seq
    robotsStore.handleRobotSelection()
  }
})
</script>
