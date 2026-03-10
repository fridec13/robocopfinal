<template>
  <div class="relative h-full">
    <div
      class="absolute top-0 right-0 h-full bg-white shadow-lg transition-all duration-300 ease-in-out overflow-hidden"
      :class="isCollapsed ? 'w-0' : 'w-[400px]'"
    >
      <div class="flex flex-col h-full">
        <!-- 헤더 -->
        <div class="flex items-center h-[55px] p-4 border-b border-gray-700 bg-gray-800 box-border">
          <h3 class="text-white font-medium text-base flex items-center gap-2 m-0">
            <span class="text-blue-400">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd"
                      d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
                      clip-rule="evenodd" />
              </svg>
            </span>
            실시간 로봇 위치
          </h3>
        </div>

        <!-- 맵 컨텐츠 -->
        <div class="flex-1 p-4 bg-gray-50">
          <div class="relative bg-white rounded-lg shadow-sm h-full flex flex-col">
            <div class="absolute inset-0 p-2">
              <RobotMap
                :showSelectedNodes="false"
                ref="robotMapRef"
                class="w-full h-full"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 접기/펼치기 버튼 -->
    <button
      class="absolute top-1/2 -translate-y-1/2 -left-5
             bg-white hover:bg-gray-50 border border-gray-200
             shadow-md rounded-l-lg w-6 h-20
             flex items-center justify-center
             text-gray-600 hover:text-gray-800
             transition-all duration-200"
      @click="toggleSidebar"
    >
      <span class="text-sm">{{ isCollapsed ? '›' : '‹' }}</span>
    </button>
  </div>
</template>

<script setup>
import RobotMap from '@/components/map/RobotMap.vue';
import { useRobotsStore } from '@/stores/robots';
import { onMounted, nextTick, watch } from 'vue';

const props = defineProps({
  isCollapsed: { type: Boolean, default: false }
});

const emit = defineEmits(['toggle-sidebar']);
const robotsStore = useRobotsStore();

const toggleSidebar = () => {
  emit('toggle-sidebar');
  nextTick(() => {
    const chart = document.querySelector('.chart');
    if (chart) chart.dispatchEvent(new Event('resize'));
  });
};

async function fetchRobotPositions() {
  // 향후 구현: 로봇 위치 데이터를 받아오는 로직
}

onMounted(() => {
  robotsStore.loadRobots();
  fetchRobotPositions();
});

watch(() => props.isCollapsed, async (newVal) => {
  if (!newVal) {
    await nextTick();
    const chart = document.querySelector('.chart');
    if (chart) chart.dispatchEvent(new Event('resize'));
  }
});
</script>

<style scoped>
.bg-gray-50 { background-color: #F9FAFB; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #94A3B8; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #64748B; }

.flex-1 { min-height: 0; }

:deep(.robot-map-container) { width: 100%; height: 100%; }
</style>
