class WebSocketService {
    constructor() {
        this.socket = null;
        this.subscribers = new Map();
    }

    async connect(url) {
        return new Promise((resolve, reject) => {
            try {
                this.socket = new WebSocket(url);
                
                this.socket.onopen = () => {
                    console.log('WebSocket ?∞Í≤∞??);
                    resolve();
                };

                this.socket.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        console.log('Î∞õÏ? ?∞Ïù¥??', data);  // ?îÎ≤ÑÍπÖÏö©
                        this.subscribers.forEach((callbacks, topic) => {
                            callbacks.forEach(callback => callback(data));
                        });
                    } catch (error) {
                        console.error('Î©îÏãúÏßÄ Ï≤òÎ¶¨ Ï§??êÎü¨:', error);
                    }
                };

                this.socket.onerror = (error) => {
                    console.error('WebSocket ?êÎü¨:', error);
                    reject(error);
                };

                this.socket.onclose = () => {
                    console.log('WebSocket ?∞Í≤∞ Ï¢ÖÎ£å');
                    this.subscribers.clear();
                };

            } catch (error) {
                reject(error);
            }
        });
    }

    subscribe(topic, callback) {
        console.log('Íµ¨ÎèÖ ?úÎèÑ:', topic);  // ?îÎ≤ÑÍπÖÏö©
        if (!this.socket) {
            throw new Error('?πÏÜåÏºìÏù¥ ?∞Í≤∞?òÏ? ?äÏïò?µÎãà??');
        }
        
        if (!this.subscribers.has(topic)) {
            this.subscribers.set(topic, new Set());
        }
        this.subscribers.get(topic).add(callback);
        
        return () => {
            const callbacks = this.subscribers.get(topic);
            if (callbacks) {
                callbacks.delete(callback);
                if (callbacks.size === 0) {
                    this.subscribers.delete(topic);
                }
            }
        };
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
            this.subscribers.clear();
        }
    }
}

// ?±Í????∏Ïä§?¥Ïä§ ?ùÏÑ± Î∞??¥Î≥¥?¥Í∏∞
const webSocketService = new WebSocketService();
export default webSocketService; 