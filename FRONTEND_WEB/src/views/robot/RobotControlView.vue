<template>
  <div class="h-full overflow-y-auto bg-gray-100 p-5">
    <div class="border-b pb-2 mb-4">
      <h2 class="text-2xl font-bold text-gray-800">로봇 제어</h2>
    </div>

    <div class="bg-white rounded-lg shadow-md p-6">
      <h3 class="text-lg font-semibold mb-4">수동 제어</h3>
      <p class="text-sm text-gray-500 mb-4">
        키보드 화살표 키를 사용하여 로봇을 제어하세요.
      </p>

      <div class="grid grid-cols-3 gap-2 w-40 mx-auto">
        <div></div>
        <button
          @keydown.up.prevent="sendCommand('forward')"
          @click="sendCommand('forward')"
          class="p-3 bg-gray-200 rounded hover:bg-gray-300 text-center font-bold"
        >
          &#8593;
        </button>
        <div></div>

        <button
          @click="sendCommand('left')"
          class="p-3 bg-gray-200 rounded hover:bg-gray-300 text-center font-bold"
        >
          &#8592;
        </button>
        <button
          @click="sendCommand('stop')"
          class="p-3 bg-red-200 rounded hover:bg-red-300 text-center font-bold text-red-700"
        >
          정지
        </button>
        <button
          @click="sendCommand('right')"
          class="p-3 bg-gray-200 rounded hover:bg-gray-300 text-center font-bold"
        >
          &#8594;
        </button>

        <div></div>
        <button
          @click="sendCommand('backward')"
          class="p-3 bg-gray-200 rounded hover:bg-gray-300 text-center font-bold"
        >
          &#8595;
        </button>
        <div></div>
      </div>

      <div class="mt-4">
        <label class="text-sm font-semibold">속도: {{ speed }}</label>
        <input type="range" v-model="speed" min="0.1" max="1.0" step="0.1" class="w-full mt-1" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const speed = ref(0.5);
const direction = ref('');

const sendCommand = async (cmd) => {
  direction.value = cmd;
  const velMap = {
    forward:  { linear: { x: speed.value, y: 0, z: 0 }, angular: { x: 0, y: 0, z: 0 } },
    backward: { linear: { x: -speed.value, y: 0, z: 0 }, angular: { x: 0, y: 0, z: 0 } },
    left:     { linear: { x: 0, y: 0, z: 0 }, angular: { x: 0, y: 0, z: speed.value } },
    right:    { linear: { x: 0, y: 0, z: 0 }, angular: { x: 0, y: 0, z: -speed.value } },
    stop:     { linear: { x: 0, y: 0, z: 0 }, angular: { x: 0, y: 0, z: 0 } },
  };
  try {
    await axios.post('/api/v1/ros/cmd_vel', velMap[cmd], {
      headers: { Authorization: `Bearer ${localStorage.getItem('accessToken')}` }
    });
  } catch (e) {
    console.error('명령 전송 실패:', e);
  }
};
</script>
