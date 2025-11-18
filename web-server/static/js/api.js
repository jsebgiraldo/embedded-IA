/**
 * API Client for ESP32 Developer Agent Dashboard
 */

const API_BASE_URL = window.location.origin;

class APIClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    // System status
    async getStatus() {
        return await this.request('/api/status');
    }

    // Agents
    async getAgents() {
        return await this.request('/api/agents');
    }

    async getAgent(agentId) {
        return await this.request(`/api/agents/${agentId}`);
    }

    async startAgent(agentId) {
        return await this.request(`/api/agents/${agentId}/start`, {
            method: 'POST'
        });
    }

    async stopAgent(agentId) {
        return await this.request(`/api/agents/${agentId}/stop`, {
            method: 'POST'
        });
    }

    // Jobs
    async getJobs(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/api/jobs${queryString ? '?' + queryString : ''}`;
        return await this.request(endpoint);
    }

    async getJob(jobId) {
        return await this.request(`/api/jobs/${jobId}`);
    }

    async createJob(jobData) {
        return await this.request('/api/jobs', {
            method: 'POST',
            body: JSON.stringify(jobData)
        });
    }

    async cancelJob(jobId) {
        return await this.request(`/api/jobs/${jobId}/cancel`, {
            method: 'POST'
        });
    }

    async deleteJob(jobId) {
        return await this.request(`/api/jobs/${jobId}`, {
            method: 'DELETE'
        });
    }

    // Logs
    async getLogs(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/api/logs${queryString ? '?' + queryString : ''}`;
        return await this.request(endpoint);
    }

    async clearLogs(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/api/logs${queryString ? '?' + queryString : ''}`;
        return await this.request(endpoint, {
            method: 'DELETE'
        });
    }

    // Metrics
    async getMetrics(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/api/metrics${queryString ? '?' + queryString : ''}`;
        return await this.request(endpoint);
    }

    async getMetricsSummary(sinceHours = 24) {
        return await this.request(`/api/metrics/summary?since_hours=${sinceHours}`);
    }
}

// Create global API client instance
const api = new APIClient(API_BASE_URL);
