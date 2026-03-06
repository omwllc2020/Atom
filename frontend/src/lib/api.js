import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const getAuthHeader = () => {
  const token = localStorage.getItem('forge_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// Chat/Code Generation
export const sendChatMessage = async (message, conversationId = null, context = null) => {
  const response = await axios.post(`${API}/chat`, {
    message,
    conversation_id: conversationId,
    context
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

// Video Generation
export const generateVideo = async (prompt, size = "1280x720", duration = 4) => {
  const response = await axios.post(`${API}/video/generate`, {
    prompt,
    size,
    duration
  }, { headers: getAuthHeader() });
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

export { API, BACKEND_URL };
