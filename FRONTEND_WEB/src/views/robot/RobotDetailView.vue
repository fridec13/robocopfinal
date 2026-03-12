<template>
  <div class="h-full overflow-y-auto bg-gray-100 p-5">
    <div v-if="robot" class="space-y-4">
      <div class="border-b pb-2 mb-4 flex items-center justify-between">
        <h1 class="text-2xl font-bold text-gray-800">
          {{ robot.nickname || robot.manufactureName }}
          <span class="text-sm" :class="robot.isActive ? 'text-green-500' : 'text-red-500'">
            ({{ robot.isActive ? '활성화' : '비활성화' }})
          </span>
        </h1>
        <button
          @click="showNicknameModal = true"
          class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
        >
          닉네임 설정
        </button>
      </div>

      <RobotInfo :robot="robot" />
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
import { useRoute } from 'vue-router';
import { useRobotsStore } from '@/stores/robots';
import RobotInfo from '@/components/detail/RobotInfo.vue';
import RobotNickname from '@/components/detail/RobotNickname.vue';

const route = useRoute();
const robotsStore = useRobotsStore();

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
</script>
