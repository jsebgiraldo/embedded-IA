/**
 * WebSocket Client for real-time updates
 */

class WebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectInterval = 3000;
        this.reconnectTimer = null;
        this.listeners = {};
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsURL = `${protocol}//${window.location.host}/ws`;

        console.log('Connecting to WebSocket:', wsURL);

        try {
            this.ws = new WebSocket(wsURL);

            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.updateConnectionStatus(true);
                
                // Clear reconnect timer if exists
                if (this.reconnectTimer) {
                    clearTimeout(this.reconnectTimer);
                    this.reconnectTimer = null;
                }
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus(false);
                this.scheduleReconnect();
            };

        } catch (error) {
            console.error('Error creating WebSocket:', error);
            this.scheduleReconnect();
        }
    }

    scheduleReconnect() {
        if (!this.reconnectTimer) {
            console.log(`Reconnecting in ${this.reconnectInterval / 1000}s...`);
            this.reconnectTimer = setTimeout(() => {
                this.reconnectTimer = null;
                this.connect();
            }, this.reconnectInterval);
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('ws-status');
        if (statusElement) {
            if (connected) {
                statusElement.innerHTML = '<span class="status-icon">🟢</span><span>Connected</span>';
            } else {
                statusElement.innerHTML = '<span class="status-icon">🔴</span><span>Disconnected</span>';
            }
        }
    }

    handleMessage(data) {
        console.log('WebSocket message:', data);

        // Handle connection message
        if (data.type === 'connection') {
            console.log(data.message);
            return;
        }

        // Emit event to registered listeners
        const eventType = data.type || data.event_type;
        if (eventType && this.listeners[eventType]) {
            this.listeners[eventType].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in listener for ${eventType}:`, error);
                }
            });
        }

        // Also emit to 'all' listeners
        if (this.listeners['all']) {
            this.listeners['all'].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('Error in all listener:', error);
                }
            });
        }
    }

    on(eventType, callback) {
        if (!this.listeners[eventType]) {
            this.listeners[eventType] = [];
        }
        this.listeners[eventType].push(callback);
    }

    off(eventType, callback) {
        if (this.listeners[eventType]) {
            this.listeners[eventType] = this.listeners[eventType].filter(
                cb => cb !== callback
            );
        }
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.error('WebSocket is not connected');
        }
    }

    disconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Create global WebSocket client instance
const wsClient = new WebSocketClient();
