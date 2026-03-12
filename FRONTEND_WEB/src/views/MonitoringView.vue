<template>
  <div class="h-full flex flex-col gap-1.5 p-5 overflow-y-auto bg-gray-100">
    <div class="border-b pb-2 mb-4">
      <h2 class="text-2xl font-bold text-gray-800">로봇 관제 대시보드</h2>
    </div>

    <div class="flex border-b">
      <button
        v-for="tab in tabs"
        :key="tab.name"
        @click="handleTabChange(tab.name)"
        class="px-6 py-3 text-gray-600 font-semibold transition-all"
        :class="{
          'border-b-4 border-blue-500 text-blue-600': activeTab === tab.name,
          'hover:text-blue-500': activeTab !== tab.name
        }"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="mt-4">
      <div v-if="activeTab === 'robotMap'" class="bg-white rounded-lg shadow-md p-5 font-sans">
        <RobotMap
          v-if="isMapReady"
          :key="mapKey"
          :showSelectedNodes="false"
          :isMonitoringMode="true"
          ref="robotMapRef"
        />
        <div v-else class="flex justify-center items-center h-64">
          <div class="text-gray-500">맵 로딩...</div>
        </div>
      </div>

      <RobotList v-if="activeTab === 'robotList'" />
      <StatisticsView v-if="activeTab === 'statistics'" />
    </div>

    <RobotManagement
      :show="robotsStore.showRobotManagementModal"
      :robots="robots"
      @close="robotsStore.closeRobotManagementModal"
      @openAddRobotModal="robotsStore.openAddRobotModal"
    />

    <RobotRegistration
      :show="robotsStore.showModal"
      :newRobot="robotsStore.newRobot"
      @handleAddRobot="robotsStore.handleAddRobot"
      @close="robotsStore.closeModal"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRobotsStore } from '@/stores/robots';
import RobotList from '@/components/dashboard/RobotList.vue';
import RobotManagement from '@/components/dashboard/RobotManagement.vue';
import RobotRegistration from '@/components/dashboard/RobotRegistration.vue';
import RobotMap from '@/components/map/RobotMap.vue';
import StatisticsView from '@/views/statistics/StatisticsView.vue';

const robotsStore = useRobotsStore();
const robots = computed(() => robotsStore.robots);
const robotMapRef = ref(null);
const isMapReady = ref(false);
const mapKey = ref(Date.now());

const activeTab = ref('robotMap');
const tabs = ref([
  { name: 'robotMap', label: '로봇 맵 탭' },
  { name: 'robotList', label: '로봇 목록' },
  { name: 'statistics', label: '통계' }
]);

async function loadRobotData() {
  try {
    await robotsStore.loadRobots();
    isMapReady.value = true;
  } catch (error) {
    console.error('로봇 데이터 로딩 오류:', error);
  }
}

async function handleTabChange(tabName) {
  activeTab.value = tabName;
  if (tabName === 'robotMap') {
    mapKey.value = Date.now();
    if (!isMapReady.value) {
      await loadRobotData();
    }
  }
}

watch(robots, (newRobots) => {
  if (newRobots.length > 0 && !isMapReady.value) {
    isMapReady.value = true;
  }
}, { immediate: true });

onMounted(async () => {
  await loadRobotData();
});

onUnmounted(() => {
  isMapReady.value = false;
});
</script>
