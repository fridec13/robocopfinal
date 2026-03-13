import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/login/LoginView.vue'
import MonitoringView from '@/views/MonitoringView.vue'
import RobotDetailView from '@/views/robot/RobotDetailView.vue'
import CameraView from '@/views/camera/CameraView.vue'
import EnrollmentView from '@/views/enrollment/EnrollmentView.vue'
import RobotControlView from '@/views/robot/RobotControlView.vue'
import StatisticsView from '@/views/statistics/StatisticsView.vue'
import ManagementView from '@/views/management/ManagementView.vue'
import MapMakerView from '@/views/MapMakerView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'monitoring',
      component: MonitoringView,
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { guestOnly: true }
    },
    {
      path: '/management',
      name: 'management',
      component: ManagementView,
      meta: { requiresAuth: true }
    },
    {
      path: '/:seq',
      name: 'detail',
      component: RobotDetailView,
      meta: { requiresAuth: true }
    },
    {
      path: '/camera',
      name: 'camera',
      component: CameraView,
      meta: { requiresAuth: true }
    },
    {
      path: '/enrollment',
      name: 'enrollment',
      component: EnrollmentView,
      meta: { requiresAuth: true }
    },
    {
      path: '/control',
      name: 'control',
      component: RobotControlView,
      meta: { requiresAuth: true }
    },
    {
      path: '/statistics',
      name: 'statistics',
      component: StatisticsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/mapmaker',
      name: 'mapmaker',
      component: MapMakerView,
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('accessToken');

  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login');
  } else if (to.meta.guestOnly && isAuthenticated) {
    next('/');
  } else {
    next();
  }
});

export default router
