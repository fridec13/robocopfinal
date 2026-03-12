import { ref } from 'vue'

class WebSocketService {
  constructor() {
    this.ws = null
    this.handlers = new Map()
    this.isConnected = false
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectTimeout = 3000
    this.messageHandlers = new Map()
    this.subscriptions = new Map()
    this.pendingMessages = []
  }

  // ?±ê????¸ìŠ¤?´ìŠ¤
  static getInstance() {
    if (!this.instance) {
      this.instance = new WebSocketService()
    }
    return this.instance
  }

  // ?¹ì†Œì¼??°ê²°
  async connect(url) {
    if (this.ws) return
    
    this.ws = new WebSocket(url)
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      const handlers = this.handlers.get(message.type) || []
      handlers.forEach(handler => handler(message))
    }

    return new Promise((resolve, reject) => {
      this.ws.onopen = () => {
        this.isConnected = true
        this.reconnectAttempts = 0
        this.processPendingMessages()
        resolve()
      }
      this.ws.onclose = () => {
        console.log('WebSocket ?°ê²° ?Šê?')
        this.isConnected = false
        this.handleReconnect()
      }
      this.ws.onerror = reject
    })
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`?¬ì—°ê²??œë„ ${this.reconnectAttempts}/${this.maxReconnectAttempts}...`)
      setTimeout(() => {
        this.connect(this.ws.url)
      }, this.reconnectTimeout)
    }
  }

  subscribe(topic, callback) {
    if (!this.subscriptions.has(topic)) {
      this.subscriptions.set(topic, new Set())
    }
    this.subscriptions.get(topic).add(callback)

    // êµ¬ë… ?œìž‘ ë©”ì‹œì§€ ?„ì†¡ (ë¹„ë™ê¸°ë¡œ ì²˜ë¦¬)
    setTimeout(() => {
      this.send('subscribe', { topic })
    }, 0)

    // êµ¬ë… ?´ì œ ?¨ìˆ˜ ë°˜í™˜
    return () => {
      this.unsubscribe(topic, callback)
    }
  }

  unsubscribe(topic, callback) {
    if (this.subscriptions.has(topic)) {
      this.subscriptions.get(topic).delete(callback)
      if (this.subscriptions.get(topic).size === 0) {
        this.subscriptions.delete(topic)
        // êµ¬ë… ?´ì œ ë©”ì‹œì§€ ?„ì†¡
        this.send('unsubscribe', { topic })
      }
    }
  }

  registerHandler(type, handler) {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, [])
    }
    this.handlers.get(type).push(handler)
  }

  removeHandler(type, handler) {
    if (this.handlers.has(type)) {
      const handlers = this.handlers.get(type)
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }

  handleMessage(message) {
    const handlers = this.handlers.get(message.type) || []
    handlers.forEach(handler => {
      try {
        handler(message)
      } catch (error) {
        console.error('Handler error:', error)
      }
    })
  }

  send(type, data) {
    const message = JSON.stringify({ type, data })
    
    if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(message)
      } catch (error) {
        console.error('Send error:', error)
        this.pendingMessages.push(message)
      }
    } else {
      this.pendingMessages.push(message)
    }
  }

  processPendingMessages() {
    while (this.pendingMessages.length > 0) {
      const message = this.pendingMessages.shift()
      this.ws.send(message)
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.subscriptions.clear()
      this.messageHandlers.clear()
      this.pendingMessages = []
    }
  }
}

export const webSocketService = WebSocketService.getInstance() 