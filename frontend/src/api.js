import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000',
});

export const startBot = () => api.post('/start');
export const stopBot = () => api.post('/stop');
export const getStatus = () => api.get('/status');

export default api;
