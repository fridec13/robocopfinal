<template>
  <div>
    <!-- ?Œë¦¼ ?ì—… -->
    <Transition name="slide-fade">
      <div v-if="notificationsStore.alerts" 
           class="fixed top-[55px] bg-red-600 text-white py-2 px-4 shadow-lg z-50"
           :style="{ left: sidebarWidth + 'px', right: '0' }">
        <div class="flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span class="font-bold text-lg">?¸ì¦???¤íŒ¨??ê±°ìˆ˜??ë°œê²¬!</span>
        </div>
      </div>
    </Transition>

    <!-- ê²½ë³´ ?´ì œ ë²„íŠ¼ -->
    <Transition name="fade">
      <button v-if="notificationsStore.alerts"
              @click="confirmDisableAlert"
              class="ml-4 bg-red-600 hover:bg-red-700 text-white px-4 py-1 rounded-md flex items-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
        ê²½ë³´ ?´ì œ
      </button>
    </Transition>

    <!-- ?•ì¸ ëª¨ë‹¬ -->
    <Transition name="fade">
      <div v-if="showConfirmModal" 
           class="fixed inset-0 flex items-center justify-center z-50">
        <div class="absolute inset-0 bg-black bg-opacity-50"></div>
        <div class="relative bg-white rounded-lg p-6 max-w-sm mx-4">
          <h3 class="text-xl font-bold mb-4 text-gray-900">ê²½ë³´ ?´ì œ ?•ì¸</h3>
          <p class="mb-6 text-gray-700">ê²½ë³´ë¥??´ì œ?˜ì‹œê² ìŠµ?ˆê¹Œ?</p>
          <div class="flex justify-end space-x-4">
            <button @click="cancelDisableAlert"
                    class="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-100 text-gray-700">
              ì·¨ì†Œ
            </button>
            <button @click="disableAlert"
                    :disabled="isLoading"
                    class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-red-400 disabled:cursor-not-allowed">
              {{ isLoading ? 'ì²˜ë¦¬ ì¤?..' : '?•ì¸' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { useNotificationsStore } from '@/stores/notifications';
import axios from 'axios';

const notificationsStore = useNotificationsStore();
const showConfirmModal = ref(false);
const isLoading = ref(false);

// ?¬ì´?œë°” ?ˆë¹„ë¥?ê³„ì‚°?˜ëŠ” ?¨ìˆ˜
const sidebarWidth = ref(245); // ê¸°ë³¸ê°’ìœ¼ë¡??¬ì´?œë°” ?ˆë¹„ ?¤ì • (?½ì? ?¨ìœ„)

// DOM?ì„œ ?¬ì´?œë°” ?”ì†Œë¥?ì°¾ì•„ ?ˆë¹„ë¥?ì¸¡ì •
const updateSidebarWidth = () => {
  // ListSidebarSection ì»´í¬?ŒíŠ¸??DOM ?”ì†Œ ì°¾ê¸°
  const sidebarElement = document.querySelector('.sidebar-container');
  if (sidebarElement) {
    sidebarWidth.value = sidebarElement.offsetWidth;
  }
};

// alert ?íƒœ ë³€??ê°ì??˜ì—¬ navbar ?¤í???ë³€ê²?
watch(() => notificationsStore.alerts, (newValue) => {
  if (newValue) {
    document.querySelector('nav')?.classList.add('alert-active');
    // ?Œë¦¼???œì‹œ?????¬ì´?œë°” ?ˆë¹„ ?…ë°?´íŠ¸
    updateSidebarWidth();
  } else {
    document.querySelector('nav')?.classList.remove('alert-active');
  }
});

// ê²½ë³´ ?´ì œ ?•ì¸ ëª¨ë‹¬ ?œì‹œ
const confirmDisableAlert = () => {
  showConfirmModal.value = true;
};

// ê²½ë³´ ?´ì œ ì·¨ì†Œ
const cancelDisableAlert = () => {
  showConfirmModal.value = false;
};

// ê²½ë³´ ?´ì œ ?¤í–‰
const disableAlert = async () => {
  try {
    isLoading.value = true;
    
    // API ?¸ì¶œ
    await axios.post('/api/v1/alert-off');
    
    // ?±ê³µ?˜ë©´ ë¡œì»¬ ?íƒœ ?…ë°?´íŠ¸
    notificationsStore.alerts = false;
    showConfirmModal.value = false;
  } catch (error) {
    console.error('ê²½ë³´ ?´ì œ ?¤íŒ¨:', error);
    alert('ê²½ë³´ ?´ì œ???¤íŒ¨?ˆìŠµ?ˆë‹¤. ?¤ì‹œ ?œë„?´ì£¼?¸ìš”.');
  } finally {
    isLoading.value = false;
  }
};

// ì»´í¬?ŒíŠ¸ê°€ ë§ˆìš´?¸ë  ?Œì? ì°??¬ê¸°ê°€ ë³€ê²½ë  ???¬ì´?œë°” ?ˆë¹„ ?…ë°?´íŠ¸
onMounted(() => {
  updateSidebarWidth();
  window.addEventListener('resize', updateSidebarWidth);
});

onUnmounted(() => {
  window.removeEventListener('resize', updateSidebarWidth);
});
</script>

<style scoped>
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

:global(nav.alert-active) {
  animation: alertBlink 1s infinite;
}

@keyframes alertBlink {
  0%, 100% {
    background-color: #111827;
  }
  50% {
    background-color: #dc2626;
  }
}
</style>