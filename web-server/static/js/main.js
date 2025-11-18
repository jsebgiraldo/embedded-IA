/**
 * Main Dashboard Logic
 */

// State
let agents = [];
let jobs = [];
let logs = [];
let currentWorkflow = {
    detect: { status: 'pending', time: null },
    analyze: { status: 'pending', time: null },
    fix: { status: 'pending', time: null },
    validate: { status: 'pending', time: null }
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Dashboard initializing...');
    
    // Connect WebSocket
    wsClient.connect();
    
    // Setup WebSocket event listeners
    setupWebSocketListeners();
    
    // Load initial data
    await refreshAll();
    
    // Auto-refresh every 3 seconds for real-time updates
    setInterval(refreshAll, 3000);
    
    console.log('✅ Dashboard initialized');
});

// Setup WebSocket event listeners
function setupWebSocketListeners() {
    // Listen to all events for logging
    wsClient.on('all', (data) => {
        console.log('Event received:', data);
    });
    
    // Agent status changes
    wsClient.on('agent_status_changed', (data) => {
        handleAgentStatusChange(data);
    });
    
    // Job events
    wsClient.on('job_started', (data) => {
        handleJobStarted(data);
    });
    
    wsClient.on('job_progress', (data) => {
        handleJobProgress(data);
    });
    
    wsClient.on('job_completed', (data) => {
        handleJobCompleted(data);
    });
    
    // Log entries
    wsClient.on('log_entry', (data) => {
        handleLogEntry(data);
    });
    
    // Workflow phase events
    wsClient.on('workflow_phase_started', (data) => {
        handleWorkflowPhaseStarted(data);
    });
    
    wsClient.on('workflow_phase_completed', (data) => {
        handleWorkflowPhaseCompleted(data);
    });
}

// Refresh all data
async function refreshAll() {
    await Promise.all([
        refreshAgents(),
        refreshJobs(),
        refreshLogs(),
        refreshMetrics()
    ]);
}

// Refresh agents
async function refreshAgents() {
    try {
        agents = await api.getAgents();
        renderAgents();
        updateAgentCount();
    } catch (error) {
        console.error('Error refreshing agents:', error);
    }
}

// Refresh jobs
async function refreshJobs() {
    try {
        jobs = await api.getJobs({ limit: 10 });
        renderJobs();
        updateJobsCount();
    } catch (error) {
        console.error('Error refreshing jobs:', error);
    }
}

// Refresh logs
async function refreshLogs() {
    try {
        const recentLogs = await api.getLogs({ limit: 50, since_minutes: 60 });
        logs = recentLogs.reverse(); // Show oldest first
        renderLogs();
    } catch (error) {
        console.error('Error refreshing logs:', error);
    }
}

// Refresh metrics
async function refreshMetrics() {
    try {
        const summary = await api.getMetricsSummary(24);
        updateMetricsDisplay(summary);
    } catch (error) {
        console.error('Error refreshing metrics:', error);
    }
}

// Render agents
function renderAgents() {
    const container = document.getElementById('agents-list');
    if (!container) return;
    
    if (agents.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px;">No agents found</p>';
        return;
    }
    
    container.innerHTML = agents.map(agent => {
        const statusIcon = agent.status === 'active' ? '🟢' : 
                          agent.status === 'error' ? '🔴' : '⚪';
        const statusClass = agent.status;
        
        return `
            <div class="agent-item">
                <div class="agent-info">
                    <span class="agent-status ${statusClass}">${statusIcon}</span>
                    <div class="agent-details">
                        <div class="agent-name">${agent.name}</div>
                        <div class="agent-type">${agent.type}</div>
                    </div>
                </div>
                <div class="agent-actions">
                    ${agent.status === 'active' 
                        ? `<button class="btn btn-small btn-danger" onclick="stopAgent('${agent.id}')">Stop</button>`
                        : `<button class="btn btn-small btn-success" onclick="startAgent('${agent.id}')">Start</button>`
                    }
                </div>
            </div>
        `;
    }).join('');
}

// Render jobs
function renderJobs() {
    const container = document.getElementById('jobs-list');
    if (!container) return;
    
    if (jobs.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px;">No recent jobs</p>';
        return;
    }
    
    container.innerHTML = jobs.map(job => {
        const statusEmoji = job.status === 'success' ? '✅' : 
                           job.status === 'failed' ? '❌' : 
                           job.status === 'running' ? '🔄' : '⏳';
        
        const duration = job.duration ? `${job.duration.toFixed(1)}s` : '--';
        const time = new Date(job.created_at).toLocaleTimeString();
        
        return `
            <div class="job-item ${job.status}">
                <div class="job-info">
                    <div class="job-type">${statusEmoji} ${job.job_type}</div>
                    <div class="job-meta">
                        ${job.model_used || 'N/A'} • ${duration} • ${time}
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="job-status ${job.status}">${job.status}</span>
                    <button class="delete-btn" onclick="deleteJob(${job.id})" title="Delete job">×</button>
                </div>
            </div>
        `;
    }).join('');
}

// Delete job
async function deleteJob(jobId) {
    if (!confirm('¿Eliminar este job?')) return;
    
    try {
        await api.deleteJob(jobId);
        await refreshJobs();
    } catch (error) {
        console.error('Error deleting job:', error);
        alert('Error al eliminar el job');
    }
}

// Clear all jobs
async function clearAllJobs() {
    if (!confirm(`¿Eliminar todos los ${jobs.length} jobs? Esta acción no se puede deshacer.`)) return;
    
    try {
        // Delete all jobs in parallel
        const deletePromises = jobs.map(job => api.deleteJob(job.id));
        await Promise.all(deletePromises);
        
        console.log(`✅ ${jobs.length} jobs eliminados`);
        await refreshJobs();
    } catch (error) {
        console.error('Error deleting jobs:', error);
        alert('Error al eliminar los jobs');
    }
}

// Render logs
function renderLogs() {
    const container = document.getElementById('logs');
    if (!container) return;
    
    if (logs.length === 0) {
        container.innerHTML = '<p style="color: #94a3b8; text-align: center; padding: 20px;">No logs available</p>';
        return;
    }
    
    container.innerHTML = logs.map(log => {
        const time = new Date(log.timestamp).toLocaleTimeString();
        return `
            <div class="log-entry ${log.level}">
                <span class="log-time">${time}</span>
                <span class="log-level">[${log.level}]</span>
                <span class="log-message">${log.message}</span>
            </div>
        `;
    }).join('');
    
    // Auto-scroll to bottom
    container.scrollTop = container.scrollHeight;
}

// Update metrics display
function updateMetricsDisplay(summary) {
    const successRate = document.getElementById('success-rate');
    const avgTime = document.getElementById('avg-time');
    const activeAgentsCount = document.getElementById('active-agents-count');
    const jobsCount = document.getElementById('jobs-count');
    
    if (successRate) successRate.textContent = `${summary.jobs.success_rate}%`;
    if (avgTime) avgTime.textContent = `${summary.performance.avg_duration_seconds}s`;
    if (activeAgentsCount) activeAgentsCount.textContent = summary.agents.active;
    
    // Jobs count shows running jobs
    const runningJobs = jobs.filter(j => j.status === 'running').length;
    if (jobsCount) jobsCount.textContent = runningJobs;
}

// Update agent count
function updateAgentCount() {
    const activeCount = agents.filter(a => a.status === 'active').length;
    const total = agents.length;
    const elem = document.getElementById('active-agents-count');
    if (elem) elem.textContent = `${activeCount}/${total}`;
}

// Update jobs count
function updateJobsCount() {
    const runningCount = jobs.filter(j => j.status === 'running').length;
    const elem = document.getElementById('jobs-count');
    if (elem) elem.textContent = runningCount;
}

// Agent actions
async function startAgent(agentId) {
    try {
        await api.startAgent(agentId);
        await refreshAgents();
        addLog('INFO', `Agent ${agentId} started`);
    } catch (error) {
        console.error('Error starting agent:', error);
        addLog('ERROR', `Failed to start agent ${agentId}`);
    }
}

async function stopAgent(agentId) {
    try {
        await api.stopAgent(agentId);
        await refreshAgents();
        addLog('INFO', `Agent ${agentId} stopped`);
    } catch (error) {
        console.error('Error stopping agent:', error);
        addLog('ERROR', `Failed to stop agent ${agentId}`);
    }
}

// Log actions
function clearLogs() {
    logs = [];
    renderLogs();
}

function exportLogs() {
    const text = logs.map(log => {
        const time = new Date(log.timestamp).toISOString();
        return `${time} [${log.level}] ${log.message}`;
    }).join('\n');
    
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
}

function filterLogs() {
    const filter = document.getElementById('log-level-filter').value;
    const entries = document.querySelectorAll('.log-entry');
    
    entries.forEach(entry => {
        if (!filter || entry.classList.contains(filter)) {
            entry.style.display = 'block';
        } else {
            entry.style.display = 'none';
        }
    });
}

// Add log entry
function addLog(level, message) {
    const log = {
        timestamp: new Date().toISOString(),
        level: level,
        message: message
    };
    logs.push(log);
    renderLogs();
}

// WebSocket event handlers
function handleAgentStatusChange(data) {
    console.log('Agent status changed:', data);
    refreshAgents();
}

function handleJobStarted(data) {
    console.log('Job started:', data);
    refreshJobs();
    if (data.data) {
        addLog('INFO', `Job started: ${data.data.job_type || 'Unknown'}`);
    }
}

function handleJobProgress(data) {
    console.log('Job progress:', data);
    if (data.data) {
        const phase = data.data.phase;
        const progress = data.data.progress;
        const message = data.data.message;
        
        updateWorkflowPhase(phase, 'running', `${progress}%`);
        addLog('INFO', message);
    }
}

function handleJobCompleted(data) {
    console.log('Job completed:', data);
    refreshJobs();
    if (data.data) {
        addLog('SUCCESS', `Job completed: ${data.data.job_type || 'Unknown'}`);
    }
}

function handleLogEntry(data) {
    if (data.data) {
        const log = {
            timestamp: data.timestamp || new Date().toISOString(),
            level: data.data.level || 'INFO',
            message: data.data.message || ''
        };
        logs.push(log);
        if (logs.length > 100) logs.shift(); // Keep last 100 logs
        renderLogs();
    }
}

function handleWorkflowPhaseStarted(data) {
    if (data.data && data.data.phase) {
        updateWorkflowPhase(data.data.phase, 'active', '--');
    }
}

function handleWorkflowPhaseCompleted(data) {
    if (data.data) {
        const phase = data.data.phase;
        const duration = data.data.duration || '--';
        const success = data.data.success !== false;
        updateWorkflowPhase(phase, success ? 'completed' : 'failed', duration);
    }
}

// Update workflow visualization
function updateWorkflowPhase(phase, status, time) {
    const phaseElement = document.querySelector(`[data-phase="${phase}"]`);
    if (!phaseElement) return;
    
    // Remove existing status classes
    phaseElement.classList.remove('active', 'completed', 'failed');
    
    // Add new status class
    if (status === 'active') {
        phaseElement.classList.add('active');
        phaseElement.querySelector('.phase-status').textContent = '🔄';
    } else if (status === 'completed') {
        phaseElement.classList.add('completed');
        phaseElement.querySelector('.phase-status').textContent = '✅';
    } else if (status === 'failed') {
        phaseElement.classList.add('failed');
        phaseElement.querySelector('.phase-status').textContent = '❌';
    } else if (status === 'running') {
        phaseElement.classList.add('active');
        phaseElement.querySelector('.phase-status').textContent = '🔄';
    }
    
    if (time) {
        phaseElement.querySelector('.phase-time').textContent = time;
    }
}

// Tab switching functionality
function switchTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab content
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Add active class to clicked button
    const selectedButton = document.querySelector(`[onclick="switchTab('${tabName}')"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
    
    // Trigger load for projects tab
    if (tabName === 'projects' && typeof loadProjects === 'function') {
        loadProjects();
        loadProjectsStats();
    }
}

