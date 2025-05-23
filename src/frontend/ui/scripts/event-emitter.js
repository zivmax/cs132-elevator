// Event emitter utility for modular use
export function createEventEmitter() {
    const listeners = [];
    return {
        connect(callback) {
            listeners.push(callback);
        },
        emit(data) {
            listeners.forEach(cb => {
                try {
                    cb(data);
                } catch (e) {
                    console.error("Error in event listener:", e);
                }
            });
        }
    };
}
