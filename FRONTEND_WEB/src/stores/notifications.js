import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useNotificationsStore = defineStore('notifications', () => {
  const alerts = ref(false);

  // alerts ?íƒœë¥??…ë°?´íŠ¸?˜ëŠ” action
  function setAlertStatus(status) {
    alerts.value = status;
  }

  // alerts ?íƒœë¥?? ê??˜ëŠ” action
  function toggleAlert() {
    alerts.value = !alerts.value;
  }

  const notifications = ref([])
  const isNotificationsOpen = ref(false)
  const lastReadTimestamp = ref(localStorage.getItem('lastReadTimestamp') || null)

  // ?½ì? ?Šì? ?Œë¦¼ ê°œìˆ˜ ê³„ì‚°
  const unreadCount = computed(() => {
    if (!lastReadTimestamp.value) return notifications.value.length
    return notifications.value.filter(notification => !notification.isRead).length
  })

  // ?Œë¦¼ ì¶”ê?
  const addNotification = (message) => {
    const notification = {
      id: Date.now(),
      message,
      isRead: false,
      timestamp: new Date().toISOString()
    }
    notifications.value.unshift(notification)
    
    // ìµœë? 5ê°œê¹Œì§€ë§?? ì?
    if (notifications.value.length > 5) {
      notifications.value.pop()
    }

    // localStorage???Œë¦¼ ?€??
    saveNotificationsToStorage()
  }

  // ëª¨ë“  ?Œë¦¼???½ìŒ ?íƒœë¡?ë³€ê²?
  const markAllAsRead = () => {
    notifications.value.forEach(notification => {
      notification.isRead = true
    })
    lastReadTimestamp.value = new Date().toISOString()
    
    // localStorage??lastReadTimestamp ?€??
    localStorage.setItem('lastReadTimestamp', lastReadTimestamp.value)
    saveNotificationsToStorage()
  }

  // ?Œë¦¼ ì°?? ê?
  const toggleNotifications = () => {
    isNotificationsOpen.value = !isNotificationsOpen.value
    if (isNotificationsOpen.value) {
      markAllAsRead()
    }
  }

  // localStorage???Œë¦¼ ?€??
  const saveNotificationsToStorage = () => {
    localStorage.setItem('notifications', JSON.stringify(notifications.value))
  }

  // localStorage?ì„œ ?Œë¦¼ ë¡œë“œ
  const loadNotificationsFromStorage = () => {
    const savedNotifications = localStorage.getItem('notifications')
    if (savedNotifications) {
      notifications.value = JSON.parse(savedNotifications)
    }
  }

  // ì»´í¬?ŒíŠ¸ ë§ˆìš´?????€?¥ëœ ?Œë¦¼ ë¡œë“œ
  loadNotificationsFromStorage()

  return {
    notifications,
    isNotificationsOpen,
    unreadCount,
    addNotification,
    markAllAsRead,
    toggleNotifications,
    alerts,
    setAlertStatus,
    toggleAlert
  }
})