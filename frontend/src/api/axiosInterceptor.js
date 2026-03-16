import axios from 'axios';

// This interceptor will catch 401 responses and attempt to refresh the token
axios.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // If error is 401 and not already retrying
        if (error.response?.status === 401 && !originalRequest._retry) {

            // Avoid infinite loops if refresh itself fails
            if (originalRequest.url.includes('/api/refresh') || originalRequest.url.includes('/api/login')) {
                return Promise.reject(error);
            }

            originalRequest._retry = true;

            try {
                // Attempt to refresh the token
                await axios.post('/api/refresh', {}, { withCredentials: true });

                // If successful, retry the original request
                return axios(originalRequest);
            } catch (refreshError) {
                // If refresh fails, we could potentially force logout or let the UI handle it
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);
