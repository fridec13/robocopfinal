<template>
  <div class="bg-white rounded-lg shadow-md p-5 font-sans">
    <div class="border-b pb-2 mb-4">
      <h4 class="text-lg font-bold">로봇 목록</h4>
    </div>

    <div :class="[
        'grid gap-6',
        'grid-cols-1',
        {'sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4': !robotsStore.leftSidebarCollapsed},
        {'md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5': robotsStore.leftSidebarCollapsed}
      ]"
    >
      <div
        v-for="robot in visibleRobots"
        :key="robot.seq"
        :class="[
          'bg-white rounded-lg p-4 shadow transition-all relative min-h-[250px]',
          { 'opacity-40': !isActive(robot), 'hover:shadow-lg': isActive(robot) }
        ]"
      >
        <!-- 닫기 버튼 (비활성 로봇만) -->
        <button
          v-if="!isActive(robot)"
          class="absolute top-2 right-2 text-gray-500 hover:text-gray-600 z-10"
          @click="hideRobot(robot.seq)"
        >×</button>

        <!-- 로봇 이름과 상태 아이콘 -->
        <div class="flex justify-between items-start mb-3">
          <div class="flex items-start gap-2">
            <div>
              <h3 class="text-lg font-semibold">{{ robot.nickname || robot.name }}</h3>
              <p class="text-sm text-gray-500">{{ robot.manufactureName }}</p>
            </div>
            <!-- 네트워크 상태 -->
            <div class="relative w-5 h-5">
              <svg viewBox="0 0 24 24" class="w-full h-full">
                <path :class="['transition-colors', robot.networkHealth >= 80 ? 'fill-green-500' : 'fill-gray-200']"
                  d="M12 3C7.95 3 4.21 4.34 1.2 6.6L3 9C5.5 7.12 8.62 6 12 6C15.38 6 18.5 7.12 21 9L22.8 6.6C19.79 4.34 16.05 3 12 3" />
                <path :class="['transition-colors', robot.networkHealth >= 60 ? 'fill-green-500' : 'fill-gray-200']"
                  d="M12 7C9.3 7 6.81 7.89 4.8 9.4L6.6 11.8C8.1 10.67 9.97 10 12 10C14.03 10 15.9 10.67 17.4 11.8L19.2 9.4C17.19 7.89 14.7 7 12 7" />
                <path :class="['transition-colors', robot.networkHealth >= 40 ? 'fill-green-500' : 'fill-gray-200']"
                  d="M12 11C10.4 11 8.85 11.45 7.4 12.2L9 14.5C9.9 13.83 10.93 13.5 12 13.5C13.07 13.5 14.1 13.83 15 14.5L16.6 12.2C15.15 11.45 13.6 11 12 11" />
                <path :class="['transition-colors', robot.networkHealth >= 20 ? 'fill-green-500' : 'fill-gray-200']"
                  d="M12 15C10.65 15 9.4 15.45 8.4 16.2L12 21L15.6 16.2C14.6 15.45 13.35 15 12 15" />
              </svg>
            </div>
          </div>
        </div>

        <div class="space-y-2 mt-4">
          <!-- 모드 -->
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">모드</span>
            <span :class="['text-xs font-semibold px-2 py-0.5 rounded-full', modeClass(robot.status)]">
              {{ modeLabel(robot.status) }}
            </span>
          </div>
          <div>
            <span class="text-sm text-gray-600">배터리</span>
            <div class="relative w-full h-4 bg-gray-200 rounded overflow-hidden">
              <div class="h-full" :class="getBatteryClass(robot.battery?.level)" :style="{ width: (robot.battery?.level || 0) + '%' }"></div>
              <span class="absolute inset-0 flex justify-center items-center text-xs text-white font-semibold">{{ robot.battery?.level }}%</span>
            </div>
          </div>
          <div>
            <span class="text-sm text-gray-600">CPU 온도</span>
            <span class="block text-gray-800 font-medium">
              {{ robot.cpuTemp ? `${robot.cpuTemp}°C` : '데이터 없음' }}
            </span>
          </div>
          <div>
            <span class="text-sm text-gray-600">현재 위치</span>
            <span class="block text-gray-800 font-medium text-xs">
              {{ formatPosition(robot.position) }}
            </span>
          </div>
        </div>

        <div class="flex gap-2 mt-4">
          <button class="flex-1 py-2 rounded text-white text-sm bg-gray-700 hover:bg-gray-800" @click="returnRobot(robot.seq)">
            복귀 명령
          </button>
          <button
            class="flex-1 py-2 rounded text-white text-sm"
            :class="getEmergencyClass(robot.status)"
            @click="handleStartStop(robot)"
          >
            {{ robot.status === 'navigating' || robot.status === 'patrolling' ? '비상 정지' : '가동 시작' }}
          </button>
        </div>

        <button class="mt-2 w-full py-2 rounded bg-gray-900 text-white text-sm hover:bg-gray-800" @click="goToDetailPage(robot.seq)">
          상세 페이지
        </button>
      </div>

      <!-- 로봇 관리 추가 -->
      <div class="flex flex-col items-center justify-center bg-gray-100 rounded-lg p-6 cursor-pointer min-h-[250px]" @click="robotsStore.openRobotManagementModal">
        <div class="text-6xl text-gray-400">+</div>
        <button class="mt-2 px-4 py-2 bg-gray-300 rounded hover:bg-gray-400 transition-colors">로봇 관리</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useRobotsStore } from '@/stores/robots';
import { useRobotCommandsStore } from '@/stores/robotCommands';
import { useToast } from 'vue-toastification';

const router = useRouter();
const robotsStore = useRobotsStore();
const robotCommandsStore = useRobotCommandsStore();
const toast = useToast();
const hiddenRobots = ref([]);

const robots = computed(() => robotsStore.displayRobots);
const visibleRobots = computed(() =>
  robots.value.filter(robot => !hiddenRobots.value.includes(robot.seq))
);

const hideRobot = (robotSeq) => hiddenRobots.value.push(robotSeq);

const getBatteryClass = (battery) => ({
  'bg-green-500': battery >= 30,
  'bg-red-500': battery < 30
});

const getEmergencyClass = (status) => ({
  'bg-red-600 hover:bg-red-700': status === 'navigating' || status === 'patrolling',
  'bg-emerald-500 hover:bg-emerald-600': status !== 'navigating' && status !== 'patrolling'
});

const getOperationTime = (startTime, isActive) => {
  if (!startTime || !isActive) return '00시간 00분';
  const diff = new Date() - new Date(startTime);
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  return `${String(hours).padStart(2, '0')}시간 ${String(minutes).padStart(2, '0')}분`;
};

// UTM → Gazebo 로컬 좌표 (미터)로 변환하여 표시
const UTM_ORIGIN_X = 304411.645
const UTM_ORIGIN_Y = 3892836.76
const formatPosition = (pos) => {
  if (!pos || (pos.x === 0 && pos.y === 0)) return '위치 없음'
  const lx = (pos.x - UTM_ORIGIN_X).toFixed(1)
  const ly = (pos.y - UTM_ORIGIN_Y).toFixed(1)
  return `x: ${lx}m, y: ${ly}m`
};

const returnRobot = async (robotSeq) => {
  if (!robotSeq) return;
  try {
    await robotCommandsStore.homingCommand(robotSeq);
    toast.info('로봇을 복귀합니다', { position: "bottom-center", timeout: 3000 });
  } catch (err) {
    console.error('복귀 명령 오류:', err);
  }
};

const handleStartStop = async (robot) => {
  const isMoving = robot.status === 'navigating' || robot.status === 'patrolling';
  if (isMoving) {
    try {
      await robotCommandsStore.tempStopCommand(robot.seq);
      robot.status = 'emergencyStopped';
      toast.info('로봇을 일시정지합니다', { position: "bottom-center", timeout: 3000 });
    } catch (err) {
      console.error('비상 정지 명령 오류:', err);
    }
  } else {
    try {
      await robotCommandsStore.initializeAI();
      await robotCommandsStore.resumeCommand(robot.seq);
      robot.status = 'navigating';
      toast.info('로봇을 재개합니다', { position: "bottom-center", timeout: 3000 });
    } catch (err) {
      console.error('가동 시작 명령 오류:', err);
    }
  }
};

const goToDetailPage = (robotSeq) => router.push(`/${robotSeq}`);

const isActive = (robot) =>
  robot.isActive === true || robot.IsActive === true;

const MODE_LABELS = {
  waiting:        '대기 중',
  homing:         '복귀 중',
  navigate:       '이동 중',
  navigating:     '이동 중',
  patrol:         '순찰 중',
  patrolling:     '순찰 중',
  manual:         '수동 조작',
  'temp stop':    '일시 정지',
  'emergency stop': '비상 정지',
}
const MODE_COLORS = {
  waiting:        'bg-gray-100 text-gray-600',
  homing:         'bg-blue-100 text-blue-700',
  navigate:       'bg-green-100 text-green-700',
  navigating:     'bg-green-100 text-green-700',
  patrol:         'bg-emerald-100 text-emerald-700',
  patrolling:     'bg-emerald-100 text-emerald-700',
  manual:         'bg-yellow-100 text-yellow-700',
  'temp stop':    'bg-orange-100 text-orange-700',
  'emergency stop': 'bg-red-100 text-red-700',
}
const modeLabel = (status) => MODE_LABELS[status] ?? (status || '알 수 없음')
const modeClass = (status) => MODE_COLORS[status] ?? 'bg-gray-100 text-gray-500'
</script>
