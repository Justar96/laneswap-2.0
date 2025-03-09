// Global variables
let services = {};
let refreshInterval = null;
let viewMode = 'grid';
let focusedServiceId = null;

// DOM elements
const apiUrlInput = document.getElementById('apiUrlInput');
const connectBtn = document.getElementById('connectBtn');
const refreshBtn = document.getElementById('refreshBtn');
const refreshIntervalSelect = document.getElementById('refreshIntervalSelect');
const viewGridBtn = document.getElementById('viewGridBtn');
const viewTableBtn = document.getElementById('viewTableBtn');
const servicesList = document.getElementById('servicesList');
const searchInput = document.getElementById('searchInput');
const clearSearchBtn = document.getElementById('clearSearchBtn');
const lastUpdated = document.getElementById('lastUpdated');
const themeSelect = document.getElementById('themeSelect');
const dateFormatSelect = document.getElementById('dateFormatSelect');
const saveSettingsBtn = document.getElementById('saveSettingsBtn');

// Initialize the app
function init() {
    // Load saved API URL from localStorage
    const savedApiUrl = localStorage.getItem('laneswap-api-url');
    if (savedApiUrl) {
        apiUrlInput.value = savedApiUrl;
    }
    
    // Load saved refresh interval from localStorage
    const savedRefreshInterval = localStorage.getItem('laneswap-refresh-interval');
    if (savedRefreshInterval) {
        refreshIntervalSelect.value = savedRefreshInterval;
    }
    
    // Load saved view mode from localStorage
    const savedViewMode = localStorage.getItem('laneswap-view-mode');
    if (savedViewMode) {
        viewMode = savedViewMode;
    }
    
    // Load saved theme from localStorage
    const savedTheme = localStorage.getItem('laneswap-theme') || 'dark';
    themeSelect.value = savedTheme;
    applyTheme(savedTheme);
    
    // Load saved date format from localStorage
    const savedDateFormat = localStorage.getItem('laneswap-date-format');
    if (savedDateFormat) {
        dateFormatSelect.value = savedDateFormat;
    }
    
    // Set up event listeners
    connectBtn.addEventListener('click', fetchServices);
    refreshBtn.addEventListener('click', fetchServices);
    refreshIntervalSelect.addEventListener('change', setRefreshInterval);
    viewGridBtn.addEventListener('click', () => setViewMode('grid'));
    viewTableBtn.addEventListener('click', () => setViewMode('table'));
    searchInput.addEventListener('input', updateServicesUI);
    clearSearchBtn.addEventListener('click', clearSearch);
    saveSettingsBtn.addEventListener('click', saveSettings);
    
    // Check for URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const apiParam = urlParams.get('api');
    const serviceParam = urlParams.get('service');
    
    if (apiParam) {
        apiUrlInput.value = apiParam;
        
        // Store the service ID to focus on after loading
        if (serviceParam) {
            localStorage.setItem('laneswap-focus-service', serviceParam);
        }
        
        // Fetch services automatically
        fetchServices();
    }
    
    // Set the refresh interval
    setRefreshInterval();
    
    // Update UI elements
    updateViewButtons();
}

// Set the refresh interval
function setRefreshInterval() {
    // Clear existing interval
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
    
    // Get the selected interval
    const interval = parseInt(refreshIntervalSelect.value, 10);
    
    // Save to localStorage
    localStorage.setItem('laneswap-refresh-interval', interval.toString());
    
    // Set new interval if not manual
    if (interval > 0) {
        refreshInterval = setInterval(fetchServices, interval * 1000);
    }
}

// Set the view mode (grid or table)
function setViewMode(mode) {
    viewMode = mode;
    localStorage.setItem('laneswap-view-mode', mode);
    
    updateViewButtons();
    updateServicesUI();
}

// Update view mode buttons
function updateViewButtons() {
    if (viewMode === 'grid') {
        viewGridBtn.classList.add('active', 'btn-primary');
        viewGridBtn.classList.remove('btn-outline-secondary');
        viewTableBtn.classList.remove('active', 'btn-primary');
        viewTableBtn.classList.add('btn-outline-secondary');
    } else {
        viewTableBtn.classList.add('active', 'btn-primary');
        viewTableBtn.classList.remove('btn-outline-secondary');
        viewGridBtn.classList.remove('active', 'btn-primary');
        viewGridBtn.classList.add('btn-outline-secondary');
    }
}

// Clear the search input
function clearSearch() {
    searchInput.value = '';
    updateServicesUI();
}

// Save settings
function saveSettings() {
    // Save theme
    const theme = themeSelect.value;
    localStorage.setItem('laneswap-theme', theme);
    applyTheme(theme);
    
    // Save date format
    const dateFormat = dateFormatSelect.value;
    localStorage.setItem('laneswap-date-format', dateFormat);
    
    // Close the modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
    modal.hide();
    
    // Update UI
    updateServicesUI();
}

// Apply theme
function applyTheme(theme) {
    if (theme === 'system') {
        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
        
        // Listen for changes in system preference
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (themeSelect.value === 'system') {
                if (e.matches) {
                    document.body.classList.add('dark-mode');
                } else {
                    document.body.classList.remove('dark-mode');
                }
            }
        });
    } else if (theme === 'dark') {
        document.body.classList.add('dark-mode');
    } else {
        document.body.classList.remove('dark-mode');
    }
}

// Format date based on settings
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    const dateFormat = localStorage.getItem('laneswap-date-format') || 'relative';
    
    if (dateFormat === 'absolute') {
        return date.toLocaleString();
    } else {
        // Relative time format
        if (diffSec < 5) {
            return getTranslation('time.now');
        } else if (diffSec < 60) {
            return `${diffSec} ${getTranslation('time.seconds')}`;
        } else if (diffMin === 1) {
            return `1 ${getTranslation('time.minute')}`;
        } else if (diffMin < 60) {
            return `${diffMin} ${getTranslation('time.minutes')}`;
        } else if (diffHour === 1) {
            return `1 ${getTranslation('time.hour')}`;
        } else if (diffHour < 24) {
            return `${diffHour} ${getTranslation('time.hours')}`;
        } else if (diffDay === 1) {
            return `1 ${getTranslation('time.day')}`;
        } else {
            return `${diffDay} ${getTranslation('time.days')}`;
        }
    }
}

// Update the last updated timestamp
function updateLastUpdated() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString();
    lastUpdated.textContent = `${getTranslation('lastUpdated').replace('Never', '')}: ${timeStr}`;
}

// Show error message
function showError(message) {
    servicesList.innerHTML = `<div class="error-message">${message}</div>`;
    
    // Reset summary counts
    document.getElementById('healthyCount').textContent = '0';
    document.getElementById('warningCount').textContent = '0';
    document.getElementById('errorCount').textContent = '0';
    document.getElementById('staleCount').textContent = '0';
    document.getElementById('totalCount').textContent = '0';
}

// Focus on a specific service
function focusOnService(serviceId) {
    focusedServiceId = serviceId;
    
    // Scroll to the service card
    const serviceCard = document.getElementById(`service-${serviceId}`);
    if (serviceCard) {
        serviceCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Highlight the card
        serviceCard.classList.add('highlight-card');
        setTimeout(() => {
            serviceCard.classList.remove('highlight-card');
        }, 2000);
        
        // Show service details
        showServiceDetails(serviceId);
    }
}

// Show service details in modal
function showServiceDetails(serviceId) {
    const service = services[serviceId];
    if (!service) return;
    
    const modal = new bootstrap.Modal(document.getElementById('serviceDetailsModal'));
    const modalBody = document.getElementById('serviceDetailsBody');
    
    // Format metadata as JSON with syntax highlighting
    let metadataHtml = `<p>${getTranslation('service.noMetadata')}</p>`;
    if (service.metadata && Object.keys(service.metadata).length > 0) {
        metadataHtml = `<pre class="metadata-json">${JSON.stringify(service.metadata, null, 2)}</pre>`;
    }
    
    // Format heartbeat history
    let heartbeatHistoryHtml = '';
    if (service.heartbeat_history && service.heartbeat_history.length > 0) {
        heartbeatHistoryHtml = `
            <h6 class="mt-4">${getTranslation('service.heartbeatHistory') || 'Heartbeat History'}</h6>
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>${getTranslation('service.timestamp') || 'Timestamp'}</th>
                            <th>${getTranslation('service.status')}</th>
                            <th>${getTranslation('service.message')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${service.heartbeat_history.map(hb => `
                            <tr>
                                <td>${formatDate(hb.timestamp)}</td>
                                <td><span class="badge bg-${getStatusColor(hb.status)}">${hb.status}</span></td>
                                <td>${hb.message || '-'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    modalBody.innerHTML = `
        <div class="row g-3">
            <div class="col-md-6">
                <h6>${getTranslation('service.id')}</h6>
                <p class="text-monospace">${serviceId}</p>
                
                <h6>${getTranslation('service.name')}</h6>
                <p>${service.name}</p>
                
                <h6>${getTranslation('service.status')}</h6>
                <p><span class="badge bg-status-${service.status.toLowerCase()}">${service.status}</span></p>
                
                <h6>${getTranslation('service.lastHeartbeat')}</h6>
                <p>${formatDate(service.last_heartbeat)}</p>
            </div>
            <div class="col-md-6">
                <h6>${getTranslation('service.message')}</h6>
                <p>${service.message || getTranslation('service.noMessage')}</p>
                
                <h6>${getTranslation('service.metadata')}</h6>
                ${metadataHtml}
            </div>
        </div>
        
        ${heartbeatHistoryHtml}
    `;
    
    modal.show();
}

// Get status color for badges
function getStatusColor(status) {
    const normalizedStatus = status.toLowerCase();
    switch (normalizedStatus) {
        case 'healthy':
            return 'status-healthy';
        case 'warning':
            return 'status-warning';
        case 'error':
            return 'status-error';
        case 'stale':
            return 'status-stale';
        default:
            return 'secondary';
    }
}

// Fetch services from the API
async function fetchServices() {
    const apiUrl = apiUrlInput.value.trim();
    
    // Ensure the API URL has the correct format
    let formattedApiUrl = apiUrl;
    if (!formattedApiUrl.startsWith('http://') && !formattedApiUrl.startsWith('https://')) {
        formattedApiUrl = 'http://' + formattedApiUrl;
    }
    
    // Show loading state
    servicesList.innerHTML = `<div class="loading">${getTranslation('loading')}</div>`;
    
    try {
        // Add debugging information
        console.log(`Fetching services from: ${formattedApiUrl}/api/services`);
        
        const response = await fetch(`${formattedApiUrl}/api/services`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`API error: ${response.status} - ${errorText}`);
            throw new Error(`API returned status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('API response:', data);
        
        // Handle the specific format from the API
        if (data && data.services) {
            services = data.services;
            updateServicesUI();
            updateSummaryUI(data.summary);
        } else {
            console.error('Unexpected API response format:', data);
            showError(getTranslation('error'));
        }
        
        updateLastUpdated();
        
        // Check if we should focus on a specific service
        const focusServiceId = localStorage.getItem('laneswap-focus-service');
        if (focusServiceId && services[focusServiceId]) {
            setTimeout(() => focusOnService(focusServiceId), 100);
            // Clear the focus after showing it once
            localStorage.removeItem('laneswap-focus-service');
        }
        
        // Save API URL to localStorage
        localStorage.setItem('laneswap-api-url', apiUrl);
    } catch (error) {
        console.error('Fetch error:', error);
        showError(`${getTranslation('error')}: ${error.message}`);
    }
}

// Update the services UI based on the current view mode and search filter
function updateServicesUI() {
    // Get search filter
    const searchFilter = searchInput.value.toLowerCase();
    
    // Filter services based on search
    const filteredServices = Object.entries(services).filter(([id, service]) => {
        const searchString = `${id} ${service.name} ${service.status} ${service.message || ''}`.toLowerCase();
        return searchString.includes(searchFilter);
    });
    
    // Check if we have any services
    if (filteredServices.length === 0) {
        servicesList.innerHTML = `<div class="col-12 text-center mt-4">${getTranslation('noServices')}</div>`;
        return;
    }
    
    // Sort services by status (error first, then warning, then stale, then healthy)
    filteredServices.sort(([, a], [, b]) => {
        const statusOrder = { 'error': 0, 'warning': 1, 'stale': 2, 'healthy': 3 };
        return (statusOrder[a.status.toLowerCase()] || 4) - (statusOrder[b.status.toLowerCase()] || 4);
    });
    
    // Render services based on view mode
    if (viewMode === 'grid') {
        renderGridView(filteredServices);
    } else {
        renderTableView(filteredServices);
    }
}

// Render services in grid view
function renderGridView(filteredServices) {
    servicesList.innerHTML = filteredServices.map(([id, service]) => `
        <div class="col-md-4 col-xl-3 mb-3">
            <div id="service-${id}" class="card service-card h-100" onclick="showServiceDetails('${id}')">
                <div class="card-header bg-status-${service.status.toLowerCase()}">
                    <h5 class="card-title text-white m-0">${service.name}</h5>
                </div>
                <div class="card-body">
                    <p class="service-id">${id}</p>
                    <p class="service-message">${service.message || getTranslation('service.noMessage')}</p>
                    <p class="service-time mb-0">${formatDate(service.last_heartbeat)}</p>
                </div>
            </div>
        </div>
    `).join('');
}

// Render services in table view
function renderTableView(filteredServices) {
    servicesList.innerHTML = `
        <div class="col-12">
            <div class="table-responsive">
                <table class="table service-table">
                    <thead>
                        <tr>
                            <th>${getTranslation('service.name')}</th>
                            <th>${getTranslation('service.status')}</th>
                            <th>${getTranslation('service.message')}</th>
                            <th>${getTranslation('service.lastHeartbeat')}</th>
                            <th>${getTranslation('service.id')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${filteredServices.map(([id, service]) => `
                            <tr id="service-${id}" onclick="showServiceDetails('${id}')">
                                <td>${service.name}</td>
                                <td><span class="badge bg-status-${service.status.toLowerCase()}">${service.status}</span></td>
                                <td>${service.message || '-'}</td>
                                <td>${formatDate(service.last_heartbeat)}</td>
                                <td class="text-monospace small">${id}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// Update the summary UI
function updateSummaryUI(summary) {
    if (!summary) return;
    
    document.getElementById('healthyCount').textContent = summary.healthy || 0;
    document.getElementById('warningCount').textContent = summary.warning || 0;
    document.getElementById('errorCount').textContent = summary.error || 0;
    document.getElementById('staleCount').textContent = summary.stale || 0;
    document.getElementById('totalCount').textContent = summary.total || 0;
}

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', init);