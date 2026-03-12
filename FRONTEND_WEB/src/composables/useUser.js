import { useRouter } from 'vue-router';
import { useRobotsStore } from '@/stores/robots';
import axios from 'axios';

export function useUser() {
  const router = useRouter();
  const robotsStore = useRobotsStore();
  
  function logout() {
    axios
      .post('/api/v1/auth/logout', null, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
        },
      })
      .then(() => {
        // ?´ë¼?´ì–¸??ì¸¡ì—??? í° ë°?ë¡œë´‡ ? íƒ ?•ë³´ ?œê±°
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('selectedRobot');

        // ë¡œë´‡ ? íƒ ?•ë³´ ì´ˆê¸°??
        robotsStore.selectedRobot = 0;
        robotsStore.handleRobotSelection(); // ?íƒœ ê°±ì‹ 

        // Axios ê¸°ë³¸ Authorization ?¤ë” ?œê±°
        delete axios.defaults.headers.common['Authorization'];

        // ?¬ìš©?ì—ê²??Œë¦¼ ë°?ë¡œê·¸???˜ì´ì§€ë¡??´ë™
        alert('ë¡œê·¸?„ì›ƒ ?˜ì—ˆ?µë‹ˆ??');
        router.push('/login');
      })
      .catch((error) => {
        console.error('ë¡œê·¸?„ì›ƒ ?¤íŒ¨:', error);
        alert('ë¡œê·¸?„ì›ƒ???¤íŒ¨?ˆìŠµ?ˆë‹¤.');
      });
  }

  return { logout };
}
