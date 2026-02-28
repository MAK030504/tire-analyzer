// When running locally via 'npm run dev', this defaults to localhost:8000
// When deployed (via Docker/Nginx), it uses the /api proxy route.
const API_BASE_URL = import.meta.env.PROD ? '/api' : 'http://localhost:8000';

/**
 * Uploads an image to the backend for tire analysis.
 * @param {File} file - The image file to analyze.
 * @returns {Promise<Object>} The analysis result.
 */
export async function analyzeTire(file) {
    if (!file) {
        throw new Error('No file provided');
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            body: formData,
            // Don't set Content-Type header manually when using FormData
            // The browser sets it automatically with the correct boundary
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Analysis failed: ${response.status} ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error calling analysis API:', error);
        throw error;
    }
}

/**
 * Checks if the backend API is up and running.
 * @returns {Promise<boolean>} True if healthy, false otherwise.
 */
export async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        return response.ok;
    } catch (error) {
        return false;
    }
}
