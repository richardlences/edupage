import axios from 'axios';

// Create a new axios instance with a custom config.
// The timeout is set to 10s. If the request takes longer than
// that to complete, it will be aborted.
const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '', // Empty string means relative path (same domain)
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Response interceptor for handling 401 (session expired)
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            // Session expired or user not authenticated
            // Clear localStorage and redirect to login
            localStorage.removeItem('user');

            // Only redirect if not already on login page
            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default api;
