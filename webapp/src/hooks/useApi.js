import { fetchAuthSession } from 'aws-amplify/auth';

export const API_URL = import.meta.env.VITE_API_URL || "https://placeholder.execute-api.us-east-1.amazonaws.com";

export const getHeaders = async () => {
    const headers = { "Content-Type": "application/json" };
    try {
        // Attempt to fetch the active Cognito session
        const session = await fetchAuthSession();
        const token = session.tokens?.accessToken?.toString();
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
    } catch (e) {
        // Not authenticated, send without token
    }
    return headers;
}

export const fetchApi = async (endpoint, options = {}) => {
    try {
        const url = `${API_URL}${endpoint}`;
        const headers = await getHeaders();
        
        const finalOptions = {
            ...options,
            headers: {
                ...headers,
                ...options.headers
            }
        };

        const response = await fetch(url, finalOptions);
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Fetch Interceptor Failed:", error);
        throw error;
    }
}
