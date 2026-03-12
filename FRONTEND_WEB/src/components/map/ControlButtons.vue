<template>
  <div class="flex space-x-3 mb-1">
    <!-- ??/?? ?? -->
    <button
      class="flex items-center justify-center gap-1.5 w-24 h-12 text-base font-bold text-white rounded-lg transition-all duration-300 ease-in-out transform hover:scale-105 hover:shadow-lg active:scale-95 active:shadow-none"
      :class="{
        'bg-gray-300 text-gray-500 cursor-not-allowed hover:scale-100': selectedNodes.length === 0,
        'bg-blue-500 shadow-md hover:shadow-blue-200': selectedNodes.length === 1,
        'bg-green-500 shadow-md hover:shadow-green-200': selectedNodes.length >= 2
      }"
      :disabled="selectedNodes.length === 0"
      @click="selectedNodes.length === 1 ? $emit('navigate') : $emit('patrol')"
    >
      <i class="mdi" :class="selectedNodes.length >= 2 ? 'mdi-routes' : 'mdi-navigation'"></i>
      {{ selectedNodes.length >= 2 ? '??' : '??' }}
    </button>

    <!-- ?? ?? -->
    <button
      class="flex items-center justify-center gap-1.5 w-24 h-12 text-base font-bold text-white bg-red-500 rounded-lg transition-all duration-300 ease-in-out transform hover:scale-105 hover:shadow-lg hover:shadow-red-200 active:scale-95 active:shadow-none shadow-md"
      @click="handleReset"
    >
      <i class="mdi mdi-refresh"></i>
      ??
    </button>

    <!-- ????/?? ?? -->
    <button
      class="flex items-center justify-center gap-1.5 w-24 h-12 text-base font-bold text-white rounded-lg transition-all duration-300 ease-in-out transform hover:scale-105 hover:shadow-lg active:scale-95 active:shadow-none shadow-md"
      :class="{
        'bg-green-500 hover:shadow-green-200': isPaused,
        'bg-orange-500 hover:shadow-orange-200': !isPaused
      }"
      @click="handlePauseToggle"
    >
      <i class="mdi" :class="isPaused ? 'mdi-play-circle' : 'mdi-pause-circle'"></i>
      {{ isPaused ? '??' : '????' }}
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useToast } from 'vue-toastification'

const toast = useToast()

const props = defineProps({
  selectedNodes: {
    type: Array,
    default: () => []
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emits = defineEmits(['navigate', 'patrol', 'reset', 'tempStop', 'resume'])

const isPaused = ref(false)

function handleReset() {
  emits('reset')
  toast.warning('??? ?????', {
    position: "bottom-center",
    timeout: 3000,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
  })
}

function handlePauseToggle() {
  if (isPaused.value) {
    emits('resume')
    toast.success('??? ?????', {
      position: "bottom-center",
      timeout: 3000,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
    })
  } else {
    emits('tempStop')
    toast.info('??? ???????', {
      position: "bottom-center",
      timeout: 3000,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
    })
  }
  isPaused.value = !isPaused.value
}
</script>
