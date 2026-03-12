<template>
  <div class="h-full overflow-y-auto bg-gray-100 p-5">
    <div v-if="robot" class="space-y-4">
      <div class="border-b pb-2 mb-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            @click="router.push('/')"
            class="flex items-center gap-1 px-3 py-1.5 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded text-sm font-medium transition"
          >
            ← 목록으로
          </button>
          <h1 class="text-2xl font-bold text-gray-800">
            {{ robot.nickname || robot.manufactureName }}
            <span class="text-sm" :class="robot.isActive ? 'text-green-500' : 'text-red-500'">
              ({{ robot.isActive ? '활성화' : '비활성화' }})
            </span>
          </h1>
        </div>
        <button
          @click="showNicknameModal = true"
          class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
        >
          닉네임 설정
        </button>
      </div>

      <RobotInfo :robot="robot" />

      <!-- 경로 제어 -->
      <div class="bg-white rounded-lg shadow-md p-5">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-lg font-semibold">경로 제어</h3>
          <div class="flex gap-2 flex-wrap justify-end">
            <button
              @click="handleNavigate"
              :disabled="selectedNodes.length !== 1"
              class="px-3 py-1.5 text-sm rounded font-medium transition"
              :class="selectedNodes.length === 1
                ? 'bg-blue-500 text-white hover:bg-blue-600'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'"
            >이동 (노드 1개)</button>
            <button
              @click="handlePatrol"
              :disabled="selectedNodes.length < 2"
              class="px-3 py-1.5 text-sm rounded font-medium transition"
              :class="selectedNodes.length >= 2
                ? 'bg-green-500 text-white hover:bg-green-600'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'"
            >순찰 (노드 2개+)</button>
            <button
              @click="handleHoming"
              class="px-3 py-1.5 text-sm bg-yellow-500 text-white rounded hover:bg-yellow-600 font-medium"
            >복귀</button>
            <button
              @click="handleTempStop"
              class="px-3 py-1.5 text-sm bg-orange-500 text-white rounded hover:bg-orange-600 font-medium"
            >일시정지</button>
            <button
              @click="handleResume"
              class="px-3 py-1.5 text-sm bg-gray-500 text-white rounded hover:bg-gray-600 font-medium"
            >재개</button>
          </div>
        </div>
        <p class="text-xs text-gray-400 mb-3">맵의 노드를 클릭해 목적지를 선택하세요. 이동=1개, 순찰=2개 이상</p>
        <RobotMap
          ref="robotMapRef"
          :robot="robot"
          :showSelectedNodes="true"
          :isMonitoringMode="false"
          :showNodes="true"
          @selectedNodesChange="onSelectedNodesChange"
        />
      </div>
    </div>
    <div v-else class="flex justify-center items-center h-64">
      <p class="text-gray-500">로봇 정보를 불러오는 중...</p>
    </div>

    <RobotNickname
      v-if="showNicknameModal"
      :robot="robot"
      @close="showNicknameModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useRobotsStore } from '@/stores/robots';
import { useRobotCommandsStore } from '@/stores/robotCommands';
import RobotInfo from '@/components/detail/RobotInfo.vue';
import RobotNickname from '@/components/detail/RobotNickname.vue';
import RobotMap from '@/components/map/RobotMap.vue';

const route = useRoute();
const router = useRouter();
const robotsStore = useRobotsStore();
const robotCommandsStore = useRobotCommandsStore();

// URL /:seq 우선, 없으면 스토어 selectedRobot 사용
const robotSeq = computed(() => {
  const seqFromRoute = route.params.seq ? parseInt(route.params.seq, 10) : null;
  return seqFromRoute || robotsStore.selectedRobot || null;
});

// 라우트로 접근 시 스토어 selectedRobot도 동기화
watch(robotSeq, (seq) => {
  if (seq && robotsStore.selectedRobot !== seq) {
    robotsStore.selectedRobot = seq;
  }
}, { immediate: true });

const robot = computed(() => {
  const seq = robotSeq.value;
  if (!seq) return null;
  return robotsStore.robots.find(r => r.seq === seq) || null;
});

const showNicknameModal = ref(false);
const robotMapRef = ref(null);
const selectedNodes = ref([]);

const onSelectedNodesChange = (nodes) => {
  selectedNodes.value = nodes;
};

const handleNavigate = () => robotMapRef.value?.handleNavigate();
const handlePatrol   = () => robotMapRef.value?.handlePatrol();
const handleHoming   = () => robotCommandsStore.homingCommand(robotSeq.value);
const handleTempStop = () => robotCommandsStore.tempStopCommand(robotSeq.value);
const handleResume   = () => robotCommandsStore.resumeCommand(robotSeq.value);
</script>
