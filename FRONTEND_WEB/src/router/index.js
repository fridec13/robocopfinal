import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/login/LoginView.vue'
import MonitoringView from '@/views/MonitoringView.vue'
import RobotDetailView from '@/views/robot/RobotDetailView.vue'
import CameraView from '@/views/camera/CameraView.vue'
import EnrollmentView from '@/views/enrollment/EnrollmentView.vue'
import RobotControlView from '@/views/robot/RobotControlView.vue'
import StatisticsView from '@/views/statistics/StatisticsView.vue'
import ManagementView from '@/views/management/ManagementView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'monitoring',
      component: MonitoringView,
      meta: { requiresAuth: true } // ë¡œê·¸???„ìš”
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
      meta: { requiresAuth: true } // ë¡œê·¸???„ìš”
    },
    {
      path: '/:seq',
      name: 'detail',
      component: RobotDetailView,
      meta: { requiresAuth: true } // ë¡œê·¸???„ìš”
    },
    {
      path: '/camera',
      name: 'camera',
      component: CameraView,
      meta: { requiresAuth: true } // ë¡œê·¸???„ìš”
    },
    {
      path: '/enrollment',
      name: 'enrollment',
      component: EnrollmentView,
      meta: { requiresAuth: true } // ë¡œê·¸???„ìš”
    },
    {
      path: '/control',
      name: 'control',
      component: RobotControlView,
      meta: { requiresAuth: true } // ë¡œê·¸???„ìš”
    },
    {
      path: '/statistics',
      name: 'statistics',
      component: StatisticsView,
      meta: { requiresAuth: true } // ë¡œê·¸???„ìš”
    }
  ]
})

// ?¤ë¹„ê²Œì´??ê°€??ì¶”ê? (ë¡œê·¸???¬ë? ?•ì¸)
router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('accessToken'); // ë¡œê·¸???íƒœ ?•ì¸

  if (to.meta.requiresAuth && !isAuthenticated) {
    // ë¡œê·¸???????íƒœ?ì„œ ?¸ì¦???„ìš”???˜ì´ì§€ë¡?ê°€?¤ê³  ?˜ë©´ ë¡œê·¸???˜ì´ì§€ë¡??´ë™
    alert('ë¡œê·¸?¸ì´ ?„ìš”?©ë‹ˆ??');
    next('/login');
  } else if (to.meta.guestOnly && isAuthenticated) {
    // ë¡œê·¸?¸ëœ ?¬ìš©?ê? ë¡œê·¸???˜ì´ì§€(`/login`)???‘ê·¼?˜ë ¤ê³??˜ë©´ ì°¨ë‹¨
    alert('?´ë? ë¡œê·¸?¸ëœ ?íƒœ?…ë‹ˆ??');
    next('/');
  } else {
    next(); // ?•ìƒ?ìœ¼ë¡??´ë™
  }
});

export default router
