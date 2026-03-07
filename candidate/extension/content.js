// content.js - Monitors real-time browser events
console.log("[Project JD] Browser Monitor Active");

// 1. Monitor Tab/Window Focus Loss
window.addEventListener('blur', () => {
    console.log("[Project JD] Window Focus Lost");
    // In a real extension, this would send to the background script
    chrome.runtime.sendMessage({ signal: 'window_focus_loss', value: 1.0 });
});

window.addEventListener('focus', () => {
    console.log("[Project JD] Window Focus Gained");
    chrome.runtime.sendMessage({ signal: 'window_focus_gain', value: 0.0 });
});

// 2. Monitor Clipboard Activity
document.addEventListener('copy', () => {
    console.log("[Project JD] Clipboard Copy Detected");
    chrome.runtime.sendMessage({ signal: 'clipboard_event', value: 1.0 });
});

document.addEventListener('paste', () => {
    console.log("[Project JD] Clipboard Paste Detected");
    chrome.runtime.sendMessage({ signal: 'clipboard_event', value: 1.0 });
});
