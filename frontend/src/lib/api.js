import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const getAuthHeader = () => {
  const token = localStorage.getItem('forge_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// Chat/Code Generation
export const sendChatMessage = async (message, conversationId = null, context = null, projectId = null, autoFix = false, agent = 'nova', mode = 'e1', ultraThinking = false) => {
  const response = await axios.post(`${API}/chat`, {
    message,
    conversation_id: conversationId,
    context,
    project_id: projectId,
    auto_fix: autoFix,
    agent,
    mode,
    ultra_thinking: ultraThinking
  }, { headers: getAuthHeader() });
  return response.data;
};

export const getConversations = async () => {
  const response = await axios.get(`${API}/conversations`, { headers: getAuthHeader() });
  return response.data;
};

export const getConversation = async (conversationId) => {
  const response = await axios.get(`${API}/conversations/${conversationId}`, { headers: getAuthHeader() });
  return response.data;
};

export const deleteConversation = async (conversationId) => {
  await axios.delete(`${API}/conversations/${conversationId}`, { headers: getAuthHeader() });
};

// Code Execution
export const executeCode = async (code, language, projectId = null) => {
  const response = await axios.post(`${API}/code/execute`, {
    code,
    language,
    project_id: projectId
  }, { headers: getAuthHeader() });
  return response.data;
};

// Auto-Fix
export const autoFixCode = async (code, language, error, projectId = null) => {
  const response = await axios.post(`${API}/code/autofix`, {
    code,
    language,
    error,
    project_id: projectId
  }, { headers: getAuthHeader() });
  return response.data;
};

// Auto-Fix Loop
export const autoFixLoop = async (code, language, projectId = null) => {
  const response = await axios.post(`${API}/code/autofix-loop`, {
    code,
    language,
    project_id: projectId
  }, { headers: getAuthHeader() });
  return response.data;
};

// Projects
export const createProject = async (name, description = null) => {
  const response = await axios.post(`${API}/projects`, {
    name,
    description
  }, { headers: getAuthHeader() });
  return response.data;
};

export const getProjects = async () => {
  const response = await axios.get(`${API}/projects`, { headers: getAuthHeader() });
  return response.data;
};

export const getProject = async (projectId) => {
  const response = await axios.get(`${API}/projects/${projectId}`, { headers: getAuthHeader() });
  return response.data;
};

export const deleteProject = async (projectId) => {
  await axios.delete(`${API}/projects/${projectId}`, { headers: getAuthHeader() });
};

export const addFileToProject = async (projectId, name, content = '', language = null) => {
  const response = await axios.post(`${API}/projects/${projectId}/files`, {
    name,
    content,
    language
  }, { headers: getAuthHeader() });
  return response.data;
};

export const updateFile = async (projectId, filename, content) => {
  const response = await axios.put(`${API}/projects/${projectId}/files/${filename}`, {
    content
  }, { headers: getAuthHeader() });
  return response.data;
};

export const deleteFile = async (projectId, filename) => {
  await axios.delete(`${API}/projects/${projectId}/files/${filename}`, { headers: getAuthHeader() });
};

// Video Generation
export const generateVideo = async (prompt, size = "1280x720", duration = 4) => {
  const response = await axios.post(`${API}/video/generate`, {
    prompt,
    size,
    duration
  }, { headers: getAuthHeader() });
  return response.data;
};

// Video from Image/Video Upload
export const generateVideoFromMedia = async (prompt, mediaFile, size = "1280x720", duration = 4) => {
  const formData = new FormData();
  formData.append('prompt', prompt);
  formData.append('size', size);
  formData.append('duration', duration.toString());
  formData.append('media', mediaFile);
  
  const response = await axios.post(`${API}/video/from-media`, formData, {
    headers: {
      ...getAuthHeader(),
      'Content-Type': 'multipart/form-data'
    }
  });
  return response.data;
};

export const getVideoStatus = async (videoId) => {
  const response = await axios.get(`${API}/video/status/${videoId}`, { headers: getAuthHeader() });
  return response.data;
};

export const getUserVideos = async () => {
  const response = await axios.get(`${API}/videos`, { headers: getAuthHeader() });
  return response.data;
};

// Image Generation
export const generateImage = async (prompt) => {
  const response = await axios.post(`${API}/image/generate`, { prompt }, { headers: getAuthHeader() });
  return response.data;
};

export const getUserImages = async () => {
  const response = await axios.get(`${API}/images`, { headers: getAuthHeader() });
  return response.data;
};

// Site Cloning
export const cloneSite = async (url) => {
  const response = await axios.post(`${API}/clone/site`, { url }, { headers: getAuthHeader() });
  return response.data;
};

export const getUserClones = async () => {
  const response = await axios.get(`${API}/clones`, { headers: getAuthHeader() });
  return response.data;
};

// User/Credits
export const getUserCredits = async () => {
  const response = await axios.get(`${API}/user/credits`, { headers: getAuthHeader() });
  return response.data;
};

export const getUserUsage = async () => {
  const response = await axios.get(`${API}/user/usage`, { headers: getAuthHeader() });
  return response.data;
};

export const getUserUsageHistory = async (limit = 50, action = null) => {
  const params = new URLSearchParams({ limit });
  if (action) params.append('action', action);
  const response = await axios.get(`${API}/user/usage/history?${params}`, { headers: getAuthHeader() });
  return response.data;
};

export const getUserPreferences = async () => {
  const response = await axios.get(`${API}/user/preferences`, { headers: getAuthHeader() });
  return response.data;
};

export const updateUserPreferences = async (preferences) => {
  const response = await axios.put(`${API}/user/preferences`, preferences, { headers: getAuthHeader() });
  return response.data;
};

// Subscription
export const getSubscriptionPlans = async () => {
  const response = await axios.get(`${API}/subscription/plans`);
  return response.data;
};

export const getSubscription = async () => {
  const response = await axios.get(`${API}/subscription`, { headers: getAuthHeader() });
  return response.data;
};

// Stripe Checkout
export const createSubscriptionCheckout = async (planId) => {
  const originUrl = window.location.origin;
  const response = await axios.post(`${API}/checkout/subscription`, {
    plan_id: planId,
    origin_url: originUrl
  }, { headers: getAuthHeader() });
  return response.data;
};

export const createCreditsCheckout = async (packageId) => {
  const originUrl = window.location.origin;
  const response = await axios.post(`${API}/checkout/credits`, {
    package_id: packageId,
    origin_url: originUrl
  }, { headers: getAuthHeader() });
  return response.data;
};

export const getCheckoutStatus = async (sessionId) => {
  const response = await axios.get(`${API}/checkout/status/${sessionId}`, { headers: getAuthHeader() });
  return response.data;
};

export const getPaymentHistory = async (limit = 20) => {
  const response = await axios.get(`${API}/payment/history?limit=${limit}`, { headers: getAuthHeader() });
  return response.data;
};

// Agents
export const getAgents = async () => {
  const response = await axios.get(`${API}/agents`);
  return response.data;
};

// Admin APIs
export const getAdminStats = async () => {
  const response = await axios.get(`${API}/admin/stats`, { headers: getAuthHeader() });
  return response.data;
};

export const getAdminUsers = async (skip = 0, limit = 50) => {
  const response = await axios.get(`${API}/admin/users?skip=${skip}&limit=${limit}`, { headers: getAuthHeader() });
  return response.data;
};

export const getAdminUser = async (userId) => {
  const response = await axios.get(`${API}/admin/users/${userId}`, { headers: getAuthHeader() });
  return response.data;
};

export const updateAdminUser = async (userId, updates) => {
  const response = await axios.put(`${API}/admin/users/${userId}`, updates, { headers: getAuthHeader() });
  return response.data;
};

export const addUserCredits = async (userId, amount) => {
  const response = await axios.post(`${API}/admin/users/${userId}/credits?amount=${amount}`, {}, { headers: getAuthHeader() });
  return response.data;
};

export const deleteAdminUser = async (userId) => {
  const response = await axios.delete(`${API}/admin/users/${userId}`, { headers: getAuthHeader() });
  return response.data;
};

export const getAdminUsage = async (days = 30) => {
  const response = await axios.get(`${API}/admin/usage?days=${days}`, { headers: getAuthHeader() });
  return response.data;
};

export { API, BACKEND_URL };
