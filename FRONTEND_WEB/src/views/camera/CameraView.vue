<template>
  <div class="h-full overflow-y-auto bg-gray-100 p-5">
    <div class="border-b pb-2 mb-4">
      <h2 class="text-2xl font-bold text-gray-800">CCTV 카메라</h2>
    </div>

    <div class="bg-white rounded-lg shadow-md p-4 mb-4">
      <label class="text-sm font-semibold text-gray-700 mr-2">화면 모드:</label>
      <select v-model="viewMode" class="border border-gray-300 rounded px-2 py-1 text-sm">
        <option value="both">양방향</option>
        <option value="front">전방만</option>
        <option value="rear">후방만</option>
      </select>
      <p class="text-sm text-gray-500 mt-2">
        실시간 카메라 피드를 표시합니다.
        <span v-if="!robotSeq" class="text-orange-500 ml-2">(좌측 사이드바에서 로봇을 선택하세요)</span>
      </p>
    </div>

    <div class="grid gap-4" :class="viewMode === 'both' ? 'grid-cols-2' : 'grid-cols-1'">
      <div v-if="viewMode !== 'rear'" class="bg-white rounded-lg shadow-md p-4 h-80">
        <Cctv :robot-seq="robotSeq" camera-type="front" />
      </div>
      <div v-if="viewMode !== 'front'" class="bg-white rounded-lg shadow-md p-4 h-80">
        <Cctv :robot-seq="robotSeq" camera-type="rear" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import Cctv from '@/components/camera/Cctv.vue';
import { useRobotsStore } from '@/stores/robots';

const viewMode = ref('both');
const robotsStore = useRobotsStore();

const robotSeq = computed(() => robotsStore.selectedRobot || 1);
</script>
