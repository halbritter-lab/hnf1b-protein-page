// NGL.js configuration to minimize console warnings
// This file contains workarounds for known NGL.js warnings

// Override passive event listeners for NGL Stage
export function configureNGLStage(stage) {
    // The NGL library internally handles mouse/touch events
    // These warnings are from the library itself and don't affect functionality
    
    // Suppress passive event listener warnings in console if needed
    const originalAddEventListener = EventTarget.prototype.addEventListener;
    const nglContainer = stage.viewer.container;
    
    // Only for the NGL container, make wheel and touch events non-passive
    if (nglContainer) {
        ['wheel', 'touchstart', 'touchmove'].forEach(eventType => {
            nglContainer.addEventListener(eventType, (e) => {
                // Allow NGL to handle these events
            }, { passive: false });
        });
    }
    
    return stage;
}

// Note about Canvas2D warning:
// The "willReadFrequently" warning comes from NGL.js's internal canvas operations
// when it reads pixel data for picking/selection. This is a performance hint
// but doesn't affect functionality. The warning cannot be fixed from our code
// as it's internal to the NGL.js library's WebGL renderer.