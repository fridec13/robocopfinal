<template>
  <div class="mt-5">
    <table class="w-full border-collapse bg-white rounded-lg shadow-md overflow-hidden">
      <thead>
        <tr class="bg-gray-300 text-center text-sm">
          <th class="p-3 border-b">선택</th>
          <th class="p-3 border-b">로봇 ID</th>
          <th class="p-3 border-b">가동 시간</th>
          <th class="p-3 border-b">프론트캐</th>
          <th class="p-3 border-b">리어캐</th>
          <th class="p-3 border-b">로그</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="record in filteredRecords" :key="record.seq" class="text-center text-sm border-b">
          <td class="p-2"><input type="checkbox" class="form-checkbox" /></td>
          <td class="p-2">{{ record.nickname }}</td>
          <td class="p-2">{{ getOperationTime(record.startAt) }}</td>
          <td class="p-2"><button class="px-3 py-1 bg-blue-500 text-white rounded">다운로드</button></td>
          <td class="p-2"><button class="px-3 py-1 bg-blue-500 text-white rounded">다운로드</button></td>
          <td class="p-2"><button class="px-3 py-1 bg-blue-500 text-white rounded">다운로드</button></td>
        </tr>
        <tr v-if="!filteredRecords || filteredRecords.length === 0">
          <td colspan="6" class="p-4 text-center text-gray-400">정보 없음</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  robots: Array,
  selectedRobot: String
})

const filteredRecords = computed(() => {
  if (!props.robots) return []
  return props.selectedRobot === 'all'
    ? props.robots
    : props.robots.filter(robot => robot.seq === props.selectedRobot)
})

const getOperationTime = (startTime) => {
  if (!startTime) return '정보 없음'
  const start = new Date(startTime)
  const now = new Date()
  const diff = now - start
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  return `${hours}시간 ${minutes}분`
}
</script>
