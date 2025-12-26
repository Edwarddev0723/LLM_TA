/**
 * API Configuration for Teacher Web App
 * Uses Vite proxy in development, can be configured for production
 */

// In development, use relative URLs which will be proxied to backend
// In production, set VITE_API_BASE_URL environment variable
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Helper function to make API requests
 * @param {string} endpoint - API endpoint (e.g., '/api/health')
 * @param {RequestInit} options - Fetch options
 * @returns {Promise<any>} Response data
 */
export async function fetchApi(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error ${response.status}`);
  }

  return response.json();
}
