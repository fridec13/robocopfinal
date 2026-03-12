<template>
  <div
    id="app"
    :class="[
      'fixed inset-0 bg-gray-100',
      { 'overflow-hidden': isLoginPage, 'overflow-auto': !isLoginPage }
    ]"
  >
    <template v-if="!isLoginPage">
      <div class="layout-container">
        <!-- Left Sidebar -->
        <ListSidebarSection
          :is-collapsed="isLeftSidebarCollapsed"
          @toggle-left-sidebar="toggleLeftSidebar"
          class="sidebar-container z-30"
        />

        <div class="flex flex-col flex-1 relative">
          <nav class="bg-gray-900 text-white px-4 lg:px-10 h-[55px] flex items-center justify-between sticky top-0 z-40">
            <div class="flex items-center">
              <div class="cursor-pointer" @click="refreshPage">
                <img src="@/assets/whitelogo.png" alt="로고" class="h-10 lg:h-14" />
              </div>
              <AlertSystem />
            </div>

            <div class="hidden lg:flex items-center space-x-8">
              <router-link
                v-for="link in navLinks"
                :key="link.path"
                :to="link.path"
                class="nav-link"
                :class="{ 'nav-link-active': route.path === link.path }"
              >
                {{ link.name }}
              </router-link>
              <AlarmNotification inline class="ml-4" />
            </div>

            <div class="lg:hidden flex items-center space-x-4">
              <AlarmNotification compact class="mr-2" />
              <button @click="toggleMobileMenu" class="p-2" aria-label="메뉴 토글">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
              </button>

              <div
                v-if="mobileMenuOpen"
                class="absolute right-0 top-[55px] bg-gray-900 w-48 rounded-b-lg shadow-lg z-40"
              >
                <router-link
                  v-for="link in navLinks"
                  :key="link.path"
                  :to="link.path"
                  class="mobile-nav-link"
                  :class="{ 'bg-white/15': route.path === link.path }"
                  @click="closeMobileMenu"
                >
                  {{ link.name }}
                </router-link>
              </div>
            </div>
          </nav>

          <div class="main-content z-10 overflow-auto">
            <router-view />
          </div>
        </div>
      </div>
    </template>

    <template v-else>
      <router-view />
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import AlarmNotification from "@/components/dashboard/AlarmNotification.vue";
import ListSidebarSection from "./components/dashboard/ListSidebarSection.vue";
import AlertSystem from "./components/ai/AlertSystem.vue";
import { useNotificationsStore } from "./stores/notifications";
import { useRobotsStore } from '@/stores/robots';

const robotsStore = useRobotsStore();
const notificationsStore = useNotificationsStore();
const route = useRoute();
const isLoginPage = computed(() => route.path === "/login");

const navLinks = [
  { path: '/', name: '현황' },
  { path: '/camera', name: 'CCTV' },
  { path: '/control', name: '제어' },
  { path: '/management', name: '관리' }
];

const storedLeftState = localStorage.getItem("left-sidebar-collapsed");
const isLeftSidebarCollapsed = ref(storedLeftState ? storedLeftState === "true" : false);
const isSidebarCollapsed = ref(false);

const toggleLeftSidebar = () => {
  if (window.innerWidth >= 1024) {
    isLeftSidebarCollapsed.value = !isLeftSidebarCollapsed.value;
    localStorage.setItem("left-sidebar-collapsed", isLeftSidebarCollapsed.value);
    robotsStore.updateSidebarStates(isLeftSidebarCollapsed.value, isSidebarCollapsed.value);
    setTimeout(() => window.dispatchEvent(new Event("resize")), 350);
  }
};

const mobileMenuOpen = ref(false);
const toggleMobileMenu = () => { mobileMenuOpen.value = !mobileMenuOpen.value; };
const closeMobileMenu = () => { mobileMenuOpen.value = false; };

const refreshPage = () => { window.location.href = "/"; };

watch(
  () => route.path,
  () => {
    closeMobileMenu();
    setTimeout(() => window.dispatchEvent(new Event("resize")), 350);
  }
);

const alertSSEConnections = new Map();

onMounted(async () => {
  const setupAlertSSE = (seq) => {
    const alertSSE = new EventSource(`/api/v1/robots/sse/${seq}/alert`);

    alertSSE.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.alert) {
        const { type, message } = data.alert;
        if (type === 'emergency') {
          notificationsStore.alerts = true;
        } else if (type === 'clear') {
          notificationsStore.alerts = false;
          notificationsStore.addNotification({
            message: '긴급 상황이 해제되었습니다',
            timestamp: new Date().toISOString()
          });
        } else if (type === 'caution') {
          notificationsStore.addNotification({
            message: '주의 알림이 발생했습니다',
            timestamp: new Date().toISOString()
          });
        }
      }
    };

    return alertSSE;
  };

  alertSSEConnections.set(1, setupAlertSSE(1));
});

onUnmounted(() => {
  alertSSEConnections.forEach(sse => sse.close());
  alertSSEConnections.clear();
});
</script>
