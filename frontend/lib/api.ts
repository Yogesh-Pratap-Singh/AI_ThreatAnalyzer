import axios from "axios";

// Configure default base URL and credentials sharing for backend APIs
const API_URL = "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

export default api;
export { API_URL };
