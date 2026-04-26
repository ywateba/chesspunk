export const API_URL = import.meta.env.VITE_API_URL || "https://placeholder.execute-api.us-east-1.amazonaws.com";

export const getHeaders = (token = null) => {
    const headers = { "Content-Type": "application/json" };
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
}

export const fetchApi = async (endpoint, options = {}) => {
    try {
        const url = `${API_URL}${endpoint}`;
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Fetch Interceptor Failed:", error);
        throw error;
    }
}
