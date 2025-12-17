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

export default api;
