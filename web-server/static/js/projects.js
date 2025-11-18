// Projects Management JavaScript

// Global state
let currentProjects = [];
let selectedProjectId = null;

// Initialize projects when tab is activated
function initProjects() {
    loadProjects();
    loadProjectsStats();
    
    // Refresh every 30 seconds
    setInterval(() => {
        if (document.getElementById('projects').classList.contains('active')) {
            loadProjects();
            loadProjectsStats();
        }
    }, 30000);
}

// Load projects stats
async function loadProjectsStats() {
    try {
        const response = await fetch('/api/projects');
        const data = await response.json();
        
        const totalProjects = data.total || 0;
        const activeProjects = data.items.filter(p => p.status === 'active').length;
        const totalBuilds = data.items.reduce((sum, p) => sum + (p.total_builds || 0), 0);
        
        // Calculate success rate
        let successCount = 0;
        let totalBuildCount = 0;
        data.items.forEach(p => {
            if (p.success_rate !== null) {
                successCount += (p.success_rate / 100) * (p.total_builds || 0);
                totalBuildCount += (p.total_builds || 0);
            }
        });
        const successRate = totalBuildCount > 0 ? Math.round((successCount / totalBuildCount) * 100) : 0;
        
        document.getElementById('total-projects').textContent = totalProjects;
        document.getElementById('active-projects').textContent = activeProjects;
        document.getElementById('total-builds').textContent = totalBuilds;
        document.getElementById('projects-success-rate').textContent = `${successRate}%`;
    } catch (error) {
        console.error('Error loading projects stats:', error);
    }
}

// Load projects list
async function loadProjects() {
    const projectsList = document.getElementById('projects-list');
    const statusFilter = document.getElementById('project-status-filter').value;
    
    try {
        let url = '/api/projects?limit=50';
        if (statusFilter) {
            url += `&status=${statusFilter}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        currentProjects = data.items;
        
        if (currentProjects.length === 0) {
            projectsList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📦</div>
                    <h3>No Projects Yet</h3>
                    <p>Create your first GitHub project to get started</p>
                    <button class="btn btn-primary" onclick="showNewProjectModal()">➕ Create Project</button>
                </div>
            `;
            return;
        }
        
        projectsList.innerHTML = currentProjects.map(project => `
            <div class="project-card" onclick="showProjectDetail('${project.id}')">
                <div class="project-header">
                    <div class="project-title">
                        <h3>📦 ${project.name}</h3>
                    </div>
                    <span class="project-status-badge ${project.status}">${project.status}</span>
                </div>
                
                <div class="project-info">
                    <div class="project-info-row">
                        <span>🔗 ${project.repo_full_name || 'N/A'}</span>
                    </div>
                    <div class="project-info-row">
                        <span>🌿 ${project.branch}</span>
                        <span>🎯 ${project.target}</span>
                    </div>
                    ${project.last_commit_sha ? `
                        <div class="project-info-row">
                            <span>📝 ${project.last_commit_sha.substring(0, 7)}</span>
                        </div>
                    ` : ''}
                </div>
                
                <div class="project-metrics">
                    <div class="project-metric">
                        <span class="project-metric-value">${project.total_builds || 0}</span>
                        <span class="project-metric-label">Builds</span>
                    </div>
                    <div class="project-metric">
                        <span class="project-metric-value">${project.success_rate !== null ? project.success_rate + '%' : 'N/A'}</span>
                        <span class="project-metric-label">Success</span>
                    </div>
                    <div class="project-metric">
                        <span class="project-metric-value">${project.avg_build_time || 'N/A'}</span>
                        <span class="project-metric-label">Avg Time</span>
                    </div>
                </div>
                
                <div class="project-actions" onclick="event.stopPropagation()">
                    <button class="btn-sync" onclick="syncProject('${project.id}')">🔄 Sync</button>
                    <button class="btn-build" onclick="triggerBuild('${project.id}')">🔨 Build</button>
                    <button class="btn-delete" onclick="deleteProject('${project.id}', '${project.name}')">🗑️</button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading projects:', error);
        projectsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <h3>Error Loading Projects</h3>
                <p>${error.message}</p>
                <button class="btn btn-primary" onclick="loadProjects()">🔄 Retry</button>
            </div>
        `;
    }
}

// Show new project modal
function showNewProjectModal() {
    const modal = document.getElementById('new-project-modal');
    modal.classList.add('show');
    modal.style.display = 'flex';
}

// Close new project modal
function closeNewProjectModal() {
    const modal = document.getElementById('new-project-modal');
    modal.classList.remove('show');
    modal.style.display = 'none';
    document.getElementById('new-project-form').reset();
}

// Create new project
async function createProject(event) {
    event.preventDefault();
    
    const name = document.getElementById('project-name').value;
    const repoUrl = document.getElementById('project-repo-url').value;
    const branch = document.getElementById('project-branch').value || 'main';
    const target = document.getElementById('project-target').value;
    const webhookSecret = document.getElementById('project-webhook-secret').value;
    
    try {
        const response = await fetch('/api/projects', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                repo_url: repoUrl,
                branch,
                target,
                webhook_secret: webhookSecret || undefined
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create project');
        }
        
        const project = await response.json();
        
        // Show success message
        addLog('SUCCESS', `✅ Project "${name}" created successfully`);
        
        // Close modal and refresh list
        closeNewProjectModal();
        loadProjects();
        loadProjectsStats();
        
        // Show project detail
        setTimeout(() => showProjectDetail(project.id), 500);
        
    } catch (error) {
        console.error('Error creating project:', error);
        addLog('ERROR', `❌ Failed to create project: ${error.message}`);
        alert(`Error: ${error.message}`);
    }
}

// Sync project (git pull)
async function syncProject(projectId) {
    try {
        addLog('INFO', `🔄 Syncing project...`);
        
        const response = await fetch(`/api/projects/${projectId}/sync`, {
            method: 'PUT'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to sync project');
        }
        
        const result = await response.json();
        
        addLog('SUCCESS', `✅ Project synced: ${result.files_changed} files changed`);
        loadProjects();
        
    } catch (error) {
        console.error('Error syncing project:', error);
        addLog('ERROR', `❌ Failed to sync: ${error.message}`);
    }
}

// Trigger build
async function triggerBuild(projectId) {
    try {
        addLog('INFO', `🔨 Triggering build...`);
        
        const response = await fetch(`/api/projects/${projectId}/build`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to trigger build');
        }
        
        const build = await response.json();
        
        addLog('SUCCESS', `✅ Build #${build.id} started for commit ${build.commit_sha.substring(0, 7)}`);
        loadProjects();
        
    } catch (error) {
        console.error('Error triggering build:', error);
        addLog('ERROR', `❌ Failed to trigger build: ${error.message}`);
    }
}

// Delete project
async function deleteProject(projectId, projectName) {
    if (!confirm(`Are you sure you want to delete project "${projectName}"?\n\nThis will remove:\n- Project configuration\n- All builds\n- All dependencies\n- All webhook events\n\nThe cloned repository will NOT be deleted from disk.`)) {
        return;
    }
    
    try {
        addLog('INFO', `🗑️ Deleting project "${projectName}"...`);
        
        const response = await fetch(`/api/projects/${projectId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete project');
        }
        
        addLog('SUCCESS', `✅ Project "${projectName}" deleted successfully`);
        loadProjects();
        loadProjectsStats();
        
    } catch (error) {
        console.error('Error deleting project:', error);
        addLog('ERROR', `❌ Failed to delete: ${error.message}`);
    }
}

// Show project detail modal
async function showProjectDetail(projectId) {
    try {
        const response = await fetch(`/api/projects/${projectId}`);
        if (!response.ok) {
            throw new Error('Failed to load project details');
        }
        
        const project = await response.json();
        
        document.getElementById('detail-project-name').textContent = `📦 ${project.name}`;
        
        const content = document.getElementById('project-detail-content');
        content.innerHTML = `
            <div class="detail-section">
                <h3>📋 Project Information</h3>
                <div class="detail-info-grid">
                    <div class="detail-info-item">
                        <div class="detail-info-label">Status</div>
                        <div class="detail-info-value">
                            <span class="project-status-badge ${project.status}">${project.status}</span>
                        </div>
                    </div>
                    <div class="detail-info-item">
                        <div class="detail-info-label">Repository</div>
                        <div class="detail-info-value">${project.repo_full_name || 'N/A'}</div>
                    </div>
                    <div class="detail-info-item">
                        <div class="detail-info-label">Branch</div>
                        <div class="detail-info-value">${project.branch}</div>
                    </div>
                    <div class="detail-info-item">
                        <div class="detail-info-label">Target</div>
                        <div class="detail-info-value">${project.target}</div>
                    </div>
                    <div class="detail-info-item">
                        <div class="detail-info-label">Clone Path</div>
                        <div class="detail-info-value">${project.clone_path || 'N/A'}</div>
                    </div>
                    <div class="detail-info-item">
                        <div class="detail-info-label">Last Commit</div>
                        <div class="detail-info-value">${project.last_commit_sha ? project.last_commit_sha.substring(0, 7) : 'N/A'}</div>
                    </div>
                </div>
                
                ${project.webhook_secret ? `
                    <h3>🔐 Webhook Configuration</h3>
                    <div class="detail-info-item">
                        <div class="detail-info-label">Webhook URL</div>
                        <div class="detail-info-value">
                            <code>http://your-server.com/api/github/webhook</code>
                        </div>
                    </div>
                    <div class="detail-info-item">
                        <div class="detail-info-label">Secret</div>
                        <div class="detail-info-value">
                            <code>${project.webhook_secret}</code>
                        </div>
                    </div>
                ` : ''}
                
                <h3>📊 Build Statistics</h3>
                <div class="detail-info-grid">
                    <div class="detail-info-item">
                        <div class="detail-info-label">Total Builds</div>
                        <div class="detail-info-value">${project.total_builds || 0}</div>
                    </div>
                    <div class="detail-info-item">
                        <div class="detail-info-label">Success Rate</div>
                        <div class="detail-info-value">${project.success_rate !== null ? project.success_rate + '%' : 'N/A'}</div>
                    </div>
                    <div class="detail-info-item">
                        <div class="detail-info-label">Avg Build Time</div>
                        <div class="detail-info-value">${project.avg_build_time || 'N/A'}</div>
                    </div>
                </div>
                
                <h3>🔨 Recent Builds</h3>
                <div class="builds-list">
                    ${project.builds && project.builds.length > 0 ? 
                        project.builds.map(build => `
                            <div class="build-item ${build.status}">
                                <div class="build-header">
                                    <span class="build-id">Build #${build.id}</span>
                                    <span class="project-status-badge ${build.status}">${build.status}</span>
                                </div>
                                <div class="build-info">
                                    <div>📝 Commit: <span class="build-commit">${build.commit_sha.substring(0, 7)}</span></div>
                                    <div>🚀 Triggered by: ${build.triggered_by}</div>
                                    ${build.github_event_type ? `<div>📢 Event: ${build.github_event_type}</div>` : ''}
                                    <div>🕐 Created: ${new Date(build.created_at).toLocaleString()}</div>
                                    ${build.completed_at ? `<div>✅ Completed: ${new Date(build.completed_at).toLocaleString()}</div>` : ''}
                                </div>
                            </div>
                        `).join('')
                        : '<p>No builds yet</p>'
                    }
                </div>
            </div>
        `;
        
        const modal = document.getElementById('project-detail-modal');
        modal.classList.add('show');
        modal.style.display = 'flex';
        
    } catch (error) {
        console.error('Error loading project detail:', error);
        alert(`Error: ${error.message}`);
    }
}

// Close project detail modal
function closeProjectDetailModal() {
    const modal = document.getElementById('project-detail-modal');
    modal.classList.remove('show');
    modal.style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const newProjectModal = document.getElementById('new-project-modal');
    const detailModal = document.getElementById('project-detail-modal');
    
    if (event.target === newProjectModal) {
        closeNewProjectModal();
    }
    if (event.target === detailModal) {
        closeProjectDetailModal();
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initProjects);
} else {
    initProjects();
}

// Listen for WebSocket messages about projects
if (typeof ws !== 'undefined') {
    const originalOnMessage = ws.onmessage;
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        // Handle project-related updates
        if (data.type === 'project_update' || data.type === 'build_update') {
            loadProjects();
            loadProjectsStats();
        }
        
        // Call original handler
        if (originalOnMessage) {
            originalOnMessage.call(this, event);
        }
    };
}
