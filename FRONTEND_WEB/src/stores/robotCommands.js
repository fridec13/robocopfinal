import { defineStore } from 'pinia'
import axios from 'axios'

export const useRobotCommandsStore = defineStore('robotCommands', () => {
  // ëª©ì ì§€ ?´ë™ ëª…ë ¹ ?¨ìˆ˜
  const navigateCommand = async (selectedNodes, currentRobotSeq) => {
    if (selectedNodes.length !== 1 || !currentRobotSeq) {
      console.warn('[RobotCommandsStore] ë¡œë´‡??? íƒ?˜ì? ?Šì•˜ê±°ë‚˜ ëª©ì ì§€ê°€ ? íƒ?˜ì? ?Šì•˜?µë‹ˆ??')
      return
    }
    try {
      const goal = {
        x: selectedNodes[0].id[0],
        y: selectedNodes[0].id[1],
        theta: 0.0
      }
      await axios.post(
        `/api/v1/${currentRobotSeq}/call-service/navigate`,
        { goal }
      )
      console.log('[RobotCommandsStore] ?´ë™ ëª…ë ¹ ?„ì†¡ ?„ë£Œ')
    } catch (error) {
      console.error('Navigation request failed:', error)
    }
  }

  // ?œì°° ëª…ë ¹ ?¨ìˆ˜
  const patrolCommand = async (selectedNodes, currentRobotSeq) => {
    if (selectedNodes.length < 2 || !currentRobotSeq) {
      console.warn('[RobotCommandsStore] ë¡œë´‡??? íƒ?˜ì? ?Šì•˜ê±°ë‚˜ ê²½ìœ ì§€ê°€ ì¶©ë¶„?˜ì? ?ŠìŠµ?ˆë‹¤.')
      return
    }
    try {
      const goals = selectedNodes.map(node => ({
        x: node.id[0],
        y: node.id[1],
        theta: 0.0
      }))
      await axios.post(
        `/api/v1/${currentRobotSeq}/call-service/patrol`,
        { goals }
      )
      console.log('[RobotCommandsStore] ?œì°° ëª…ë ¹ ?„ì†¡ ?„ë£Œ')
    } catch (error) {
      console.error('Patrol request failed:', error)
    }
  }

  // ?¼ì‹œ?•ì? ëª…ë ¹ ?¨ìˆ˜
  const tempStopCommand = async (currentRobotSeq) => {
    if (!currentRobotSeq) {
      console.warn('[RobotCommandsStore] ë¡œë´‡??? íƒ?˜ì? ?Šì•˜?µë‹ˆ??')
      return
    }
    try {
      await axios.post(
        `/api/v1/${currentRobotSeq}/call-service/temp-stop`
      )
      console.log('[RobotCommandsStore] ?¼ì‹œ?•ì? ?”ì²­ ?„ë£Œ')
    } catch (error) {
      console.error('Temporary stop request failed:', error)
    }
  }

  // reset => estop ??resumeê¹Œì?
  const resetSelectionCommand = async (currentRobotSeq) => {
    if (!currentRobotSeq) {
      console.warn('[RobotCommandsStore] ë¡œë´‡??? íƒ?˜ì? ?Šì•˜?µë‹ˆ??')
      return []
    }
    try {
      await axios.post(
        `/api/v1/${currentRobotSeq}/reset`
      )
      console.log('[RobotCommandsStore] ë¦¬ì…‹ ëª…ë ¹ ?„ì†¡ ?„ë£Œ')
      return [] // API ?¸ì¶œ ?„ì—??? íƒ???¸ë“œ ë°°ì—´?€ ë¹„ì›Œì¤?
    } catch (error) {
      console.error('Reset request failed:', error)
      return [] // ?ëŸ¬ê°€ ë°œìƒ?´ë„ ? íƒ???¸ë“œ ë°°ì—´?€ ë¹„ì›Œì¤?
    }
  }

  // ë³µê? ëª…ë ¹ ?¨ìˆ˜ (homing)
  const homingCommand = async (currentRobotSeq) => {
    if (!currentRobotSeq) {
      console.warn('[RobotCommandsStore] ë¡œë´‡??? íƒ?˜ì? ?Šì•˜?µë‹ˆ??')
      return
    }
    try {
      await axios.post(
        `/api/v1/${currentRobotSeq}/call-service/homing`
      )
      console.log('[RobotCommandsStore] ë³µê? ëª…ë ¹ ?„ì†¡ ?„ë£Œ')
    } catch (error) {
      console.error('Homing request failed:', error)
    }
  }

  // ë¹„ìƒ ?•ì? ëª…ë ¹ ?¨ìˆ˜ (estop)
  const estopCommand = async (currentRobotSeq) => {
    if (!currentRobotSeq) {
      console.warn('[RobotCommandsStore] ë¡œë´‡??? íƒ?˜ì? ?Šì•˜?µë‹ˆ??')
      return
    }
    try {
      await axios.post(
        `/api/v1/${currentRobotSeq}/call-service/estop`
      )
      console.log('[RobotCommandsStore] ë¹„ìƒ ?•ì? ëª…ë ¹ ?„ì†¡ ?„ë£Œ')
    } catch (error) {
      console.error('Estop request failed:', error)
    }
  }

  const resumeCommand = async (currentRobotSeq) => {
    if (!currentRobotSeq) {
      console.warn('[RobotCommandsStore] ë¡œë´‡??? íƒ?˜ì? ?Šì•˜?µë‹ˆ??')
      return
    }
    try {
      await axios.post(
        `/api/v1/${currentRobotSeq}/call-service/resume`
      )
      console.log('[RobotCommandsStore] ?ë™ ëª¨ë“œ ëª…ë ¹ ?„ì†¡ ?„ë£Œ')
    } catch (error) {
      console.error('Resume request failed:', error)
    }
  }

  const robotBreakdownCommand = async (robotSeq) => {
    if (!robotSeq) {
      console.warn('[RobotCommandsStore] ë¡œë´‡??? íƒ?˜ì? ?Šì•˜?µë‹ˆ??')
      return
    }
    try {
      await axios.post(
        `/api/v1/${robotSeq}/call-service/estop`
      )
      console.log('[RobotCommandsStore] ë¡œë´‡ ê³ ìž¥ ëª…ë ¹ ?„ì†¡ ?„ë£Œ')
      return 'error' // ?íƒœ ë°˜í™˜
    } catch (error) {
      console.error('Robot breakdown request failed:', error)
      throw error
    }
  }
  
  const robotActivateCommand = async (robotSeq) => {
    if (!robotSeq) {
      console.warn('[RobotCommandsStore] ë¡œë´‡??? íƒ?˜ì? ?Šì•˜?µë‹ˆ??')
      return
    }
    try {
      await axios.post(
        `/api/v1/${robotSeq}/call-service/waiting`
      )
      console.log('[RobotCommandsStore] ë¡œë´‡ ê°€??ëª…ë ¹ ?„ì†¡ ?„ë£Œ')
      return 'waiting' // ?íƒœ ë°˜í™˜
    } catch (error) {
      console.error('Robot activate request failed:', error)
      throw error
    }
  }

  // AI ì´ˆê¸°???¨ìˆ˜
  const initializeAI = async () => {
    try {
      await axios.post(
        '/api/v1/ai-init'
      )
      console.log('[RobotCommandsStore] AI ì´ˆê¸°???„ë£Œ')
    } catch (error) {
      console.error('AI initialization failed:', error)
      throw error
    }
  }

  return {
    navigateCommand,
    patrolCommand,
    tempStopCommand,
    resetSelectionCommand,
    homingCommand,
    estopCommand,
    robotBreakdownCommand,
    robotActivateCommand,
    resumeCommand,
    initializeAI
  }
})
