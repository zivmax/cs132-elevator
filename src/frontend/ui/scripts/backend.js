// Backend WebSocket communication module
import { createEventEmitter } from './event-emitter.js';

export const backend = {
    socket: null,
    _isConnected: false,
    elevatorUpdated: createEventEmitter(),
    floorCalled: createEventEmitter(),
    _pendingPromise: null,

    init(url) {
        this.socket = new WebSocket(url);
        this.socket.onopen = () => {
            this._isConnected = true;
            console.log("js: WebSocket connection established to", url);
        };
        this.socket.onmessage = (event) => {
            let message;
            try {
                message = JSON.parse(event.data);
            } catch (e) {
                console.error("js: Error parsing JSON from backend:", e, "Raw data:", event.data);
                if (this._pendingPromise && typeof this._pendingPromise.reject === 'function') {
                    this._pendingPromise.reject(new Error("Error parsing JSON from backend: " + e.message));
                    this._pendingPromise = null;
                }
                return;
            }
            if (this._pendingPromise && message && typeof message.status === 'string') {
                if (message.status === 'success') {
                    this._pendingPromise.resolve(message);
                } else {
                    const errorMessage = message.message || 'Backend request failed';
                    this._pendingPromise.reject(new Error(errorMessage));
                }
                this._pendingPromise = null;
            } else if (message && message.type === "elevatorUpdated") {
                this.elevatorUpdated.emit(message.payload);
            } else if (message && message.type === "floorCalled") {
                this.floorCalled.emit(message.payload);
            } else {
                if (this._pendingPromise) {
                    const errorDetail = message ? JSON.stringify(message) : String(message);
                    this._pendingPromise.reject(new Error('Malformed or unexpected reply from backend. Message: ' + errorDetail));
                    this._pendingPromise = null;
                }
            }
        };
        this.socket.onclose = (event) => {
            this._isConnected = false;
            if (this._pendingPromise) {
                this._pendingPromise.reject(new Error("WebSocket connection closed"));
                this._pendingPromise = null;
            }
        };
        this.socket.onerror = (error) => {
            this._isConnected = false;
            if (this._pendingPromise) {
                this._pendingPromise.reject(new Error("WebSocket error"));
                this._pendingPromise = null;
            }
        };
    },
    sendToBackend(messageString) {
        return new Promise((resolve, reject) => {
            if (!this.isConnected()) {
                return reject(new Error("WebSocket not connected"));
            }
            if (this._pendingPromise) {
                return reject(new Error("Another request is already in flight"));
            }
            this._pendingPromise = { resolve, reject };
            try {
                this.socket.send(messageString);
            } catch (e) {
                this._pendingPromise.reject(e);
                this._pendingPromise = null;
                return;
            }
            setTimeout(() => {
                if (this._pendingPromise && this._pendingPromise.reject === reject) {
                    this._pendingPromise.reject(new Error("Request timed out"));
                    this._pendingPromise = null;
                }
            }, 10000);
        });
    },
    isConnected() {
        return this._isConnected && this.socket && this.socket.readyState === WebSocket.OPEN;
    }
};
