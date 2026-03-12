export class RobotControl {
    constructor(robotSeq, options = {}) {
        this.ws = null;
        this.robotSeq = robotSeq;
        this.options = options;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectTimeout = 1000; // 1Ï¥?
    }

    connect() {
        try {
            // FastAPI ?úÎ≤Ñ??WebSocket ?îÎìú?¨Ïù∏?∏Ïóê ?∞Í≤∞
            // this.ws = new WebSocket(`ws://localhost:8000/ws/control/${this.robotId}`);
            this.ws = new WebSocket(`wss://robocop-backend-app.fly.dev/ws/control/${this.robotSeq}`);
            this.ws.onopen = () => {
                console.log('?úÏñ¥ ?∞Í≤∞ ?±Í≥µ');
                this.reconnectAttempts = 0;
                this.setupKeyboardControls();
                this.options.onConnect?.();
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.status === 'error') {
                    console.error('?úÏñ¥ ?êÎü¨:', data.message);
                    this.options.onError?.(data.message);
                } else {
                    this.options.onFeedback?.(data);
                }
            };
            
            this.ws.onclose = () => {
                console.log('?úÏñ¥ ?∞Í≤∞ Ï¢ÖÎ£å');
                this.cleanup();
                this.options.onDisconnect?.();
                this.tryReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket ?êÎü¨:', error);
                this.options.onError?.('WebSocket ?∞Í≤∞ ?êÎü¨');
            };
        } catch (error) {
            console.error('?∞Í≤∞ ?úÎèÑ Ï§??êÎü¨:', error);
            this.options.onError?.('?∞Í≤∞ ?úÎèÑ Ï§??êÎü¨ Î∞úÏÉù');
        }
    }

    tryReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`?¨Ïó∞Í≤??úÎèÑ ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            setTimeout(() => this.connect(), this.reconnectTimeout);
        }
    }

    setupKeyboardControls() {
        document.addEventListener('keydown', this.handleKeyDown);
        document.addEventListener('keyup', this.handleKeyUp);
    }

    handleKeyDown = (event) => {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        
        const validKeys = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];
        if (validKeys.includes(event.key)) {
            event.preventDefault();
            console.log(`[Frontend] Sending keydown event: ${event.key}`);
            this.ws.send(JSON.stringify({
                key: event.key,
                action: 'keydown'
            }));
        }
    };

    handleKeyUp = (event) => {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        
        const validKeys = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];
        if (validKeys.includes(event.key)) {
            event.preventDefault();
            console.log(`[Frontend] Sending keyup event: ${event.key}`);
            this.ws.send(JSON.stringify({
                key: event.key,
                action: 'keyup'
            }));
        }
    };

    cleanup() {
        document.removeEventListener('keydown', this.handleKeyDown);
        document.removeEventListener('keyup', this.handleKeyUp);
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.cleanup();
    }

    isConnected() {
        return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
    }
}
