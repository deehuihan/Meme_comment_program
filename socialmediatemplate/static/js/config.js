// Configuration loader
let configData = null;

async function loadConfig() {
    if (configData) {
        return configData;
    }
    
    try {
        const response = await fetch('/api/config');
        configData = await response.json();
        
        return configData;
    } catch (error) {
        console.error('Error loading configuration:', error);
        return {
        };
    }
}