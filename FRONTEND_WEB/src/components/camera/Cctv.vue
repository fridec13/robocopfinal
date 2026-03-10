<template>
  <div class="w-full h-full p-4 flex flex-col">
    <div class="mb-1">
      <h3 class="text-lg font-semibold">
        {{ cameraType === 'front' ? '전방' : '후방' }} 카메라
      </h3>
    </div>
    <div class="flex-1 min-h-0 bg-black rounded-lg overflow-hidden flex items-center justify-center relative">
      <img
        v-if="!error && isValidProps"
        :src="videoUrl"
        alt="카메라 스트림"
        class="w-full h-full object-contain"
        @error="handleError"
        @load="isLoading = false"
      />
      <div v-else-if="!isValidProps" class="text-white text-center p-4">
        <p>카메라 정보가 올바르지 않습니다</p>
      </div>
      <div v-else-if="error" class="text-white text-center p-4">
        <p>카메라 피드를 불러올 수 없습니다</p>
        <button @click="retryLoad" class="mt-2 px-4 py-2 bg-blue-500 rounded-lg hover:bg-blue-600">
          다시 시도
        </button>
      </div>
      <div v-if="isLoading && !error && isValidProps" class="absolute inset-0 flex items-center justify-center text-white bg-black bg-opacity-50">
        로딩 중...
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  robotSeq: {
    type: [String, Number],
    default: 1
  },
  cameraType: {
    type: String,
    default: 'front',
    validator: (value) => ['front', 'rear'].includes(value)
  }
});

const error = ref(false);
const isLoading = ref(true);

const isValidProps = computed(() =>
  props.robotSeq &&
  props.cameraType &&
  props.robotSeq !== 'undefined' &&
  props.cameraType !== 'undefined'
);

const videoUrl = computed(() => {
  if (!isValidProps.value) return '';
  return `/api/v1/cameras/video_feed/${props.robotSeq}/${props.cameraType}`;
});

const handleError = () => {
  error.value = true;
  isLoading.value = false;
};

const retryLoad = () => {
  error.value = false;
  isLoading.value = true;
};
</script>
