import axios from 'axios';

const api = axios.create({
  baseURL: 'https://bhoomiguard-ai-backend.onrender.com/api',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('bhoomiguard_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('bhoomiguard_token');
      localStorage.removeItem('bhoomiguard_user');
      window.dispatchEvent(new Event('auth-unauthorized'));
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (credentials) => api.post('/auth/login', credentials),
  getMe: () => api.get('/auth/me'),
};

export const metadataApi = {
  getMetadata: () => api.get('/metadata'),
};

export const predictionApi = {
  predict: (data) => api.post('/predict', data),
  getPredictions: (params) => api.get('/predictions', { params }),
  getPredictionDetail: (id) => api.get(`/predictions/${id}`),
};

export const analyticsApi = {
  getOverview: (params) => api.get('/analytics/overview', { params }),
  getDistricts: () => api.get('/analytics/districts'),
  getDistrictDetail: (district) => api.get(`/analytics/district/${district}`),
  getStages: (params) => api.get('/analytics/stages', { params }),
  getRiskDistribution: (params) => api.get('/analytics/risk-distribution', { params }),
  getFeatureImportance: () => api.get('/analytics/feature-importance'),
};

export const modelApi = {
  getMetrics: () => api.get('/model/metrics'),
  getComparison: () => api.get('/model/comparison'),
  getHistory: () => api.get('/model/history'),
  retrainModel: (data) => api.post('/model/retrain', data),
  getRetrainStatus: () => api.get('/model/retrain/status'),
};

export default api;
