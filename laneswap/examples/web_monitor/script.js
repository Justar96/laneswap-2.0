// DOM Elements
const apiUrlInput = document.getElementById('api-url');
const refreshBtn = document.getElementById('refresh-btn');
const autoRefreshCheckbox = document.getElementById('auto-refresh');
const lastUpdatedSpan = document.getElementById('last-updated');
const servicesList = document.getElementById('services-list');
const serviceDetailsSection = document.getElementById('service-details-section');
const closeDetailsBtn = document.getElementById('close-details-btn');

// Summary elements
const totalCount = document.getElementById('total-count');
const healthyCount = document.getElementById('healthy-count');
const degradedCount = document.getElementById('degraded-count');
const errorCount = document.getElementById('error-count');
const staleCount = document.getElementById('stale-count');

// Detail elements
const detailServiceName = document.getElementById('detail-service-name');
const detailStatus = document.getElementById('detail-status');
const detailLastHeartbeat = document.getElementById('detail-last-heartbeat');
const detailServiceId = document.getElementById('detail-service-id');
const detailMetadata = document.getElementById('detail-metadata');
const detailEvents = document.getElementById('detail-events');

// State
let services = {};
let autoRefreshInterval = null;
const AUTO_REFRESH_INTERVAL = 10000; // 10 seconds

// Initialize
function init() {
    // Load saved API URL from localStorage if available
    const savedApiUrl = localStorage.getItem('laneswap-api-url');
    if (savedApiUrl) {
        apiUrlInput.value = savedApiUrl;
    }
    
    // Set up event listeners
    refreshBtn.addEventListener('click', fetchServices);
    autoRefreshCheckbox.addEventListener('change', toggleAutoRefresh);
    closeDetailsBtn.addEventListener('click', closeServiceDetails);
    
    // Start auto-refresh if enabled
    if (autoRefreshCheckbox.checked) {
        startAutoRefresh();
    }
    
    // Initial fetch
    fetchServices();
}

// Toggle auto-refresh
function toggleAutoRefresh() {
    if (autoRefreshCheckbox.checked) {
        startAutoRefresh();
    } else {
        stopAutoRefresh();
    }
}

// Start auto-refresh
function startAutoRefresh() {
    stopAutoRefresh(); // Clear any existing interval
    autoRefreshInterval = setInterval(fetchServices, AUTO_REFRESH_INTERVAL);
}

// Stop auto-refresh
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// Fetch services from API
async function fetchServices() {
    const apiUrl = apiUrlInput.value.trim();
    if (!apiUrl) {
        showError('Please enter a valid API URL');
        return;
    }
    
    // Save API URL to localStorage
    localStorage.setItem('laneswap-api-url', apiUrl);
    
    // Show loading state
    servicesList.innerHTML = '<div class="loading">Loading services...</div>';
    
    try {
        const response = await fetch(`${apiUrl}/api/services`);
        if (!response.ok) {
            throw new Error(`API returned status: ${response.status}`);
        }
        
        const data = await response.json();
        services = data.services || {};
        
        // Update UI
        updateServicesUI();
        updateSummaryUI(data.summary);
        updateLastUpdated();
    } catch (error) {
        showError(`Failed to fetch services: ${error.message}`);
    }
}

// Update services list UI
function updateServicesUI() {
    if (Object.keys(services).length === 0) {
        servicesList.innerHTML = '<div class="loading">No services found</div>';
        return;
    }
    
    servicesList.innerHTML = '';
    
    // Convert to array and sort by status (error first, then degraded, then stale, then others)
    const servicesArray = Object.entries(services).map(([id, service]) => ({
        id,
        ...service
    }));
    
    const statusPriority = {
        'error': 0,
        'degraded': 1,
        'stale': 2,
        'busy': 3,
        'healthy': 4,
        'unknown': 5
    };
    
    servicesArray.sort((a, b) => {
        const aPriority = statusPriority[a.status] ?? 999;
        const bPriority = statusPriority[b.status] ?? 999;
        return aPriority - bPriority;
    });
    
    // Create service cards
    servicesArray.forEach(service => {
        const serviceCard = document.createElement('div');
        serviceCard.className = 'service-card';
        serviceCard.dataset.serviceId = service.id;
        
        // Format last heartbeat time
        let lastHeartbeatStr = 'Never';
        if (service.last_heartbeat) {
            const lastHeartbeat = new Date(service.last_heartbeat);
            lastHeartbeatStr = formatTimeAgo(lastHeartbeat);
        }
        
        serviceCard.innerHTML = `
            <h3>
                ${escapeHtml(service.name)}
                <span class="status-badge ${service.status}">${service.status}</span>
            </h3>
            <div class="last-update">Last update: ${lastHeartbeatStr}</div>
            ${service.last_message ? `<div class="message">${escapeHtml(service.last_message)}</div>` : ''}
        `;
        
        // Add click event to show service details
        serviceCard.addEventListener('click', () => {
            showServiceDetails(service.id);
        });
        
        servicesList.appendChild(serviceCard);
    });
}

// Update summary UI
function updateSummaryUI(summary = {}) {
    const counts = summary.status_counts || {};
    
    totalCount.textContent = summary.total || 0;
    healthyCount.textContent = counts.healthy || 0;
    degradedCount.textContent = counts.degraded || 0;
    errorCount.textContent = counts.error || 0;
    staleCount.textContent = counts.stale || 0;
}

// Show service details
function showServiceDetails(serviceId) {
    const service = services[serviceId];
    if (!service) return;
    
    // Update detail elements
    detailServiceName.textContent = service.name;
    detailStatus.textContent = service.status;
    detailStatus.className = service.status;
    
    // Format last heartbeat
    if (service.last_heartbeat) {
        const lastHeartbeat = new Date(service.last_heartbeat);
        detailLastHeartbeat.textContent = lastHeartbeat.toLocaleString();
    } else {
        detailLastHeartbeat.textContent = 'Never';
    }
    
    detailServiceId.textContent = serviceId;
    
    // Display metadata
    if (service.metadata && Object.keys(service.metadata).length > 0) {
        detailMetadata.innerHTML = '';
        
        for (const [key, value] of Object.entries(service.metadata)) {
            // Skip sensitive fields
            if (['password', 'token', 'secret', 'key'].includes(key)) continue;
            
            const metadataItem = document.createElement('div');
            metadataItem.className = 'metadata-item';
            metadataItem.innerHTML = `<span>${escapeHtml(key)}:</span> ${escapeHtml(String(value))}`;
            detailMetadata.appendChild(metadataItem);
        }
    } else {
        detailMetadata.innerHTML = '<p>No metadata available</p>';
    }
    
    // Display events
    if (service.events && service.events.length > 0) {
        detailEvents.innerHTML = '';
        
        // Sort events by timestamp descending
        const sortedEvents = [...service.events].sort((a, b) => {
            return new Date(b.timestamp) - new Date(a.timestamp);
        });
        
        sortedEvents.forEach(event => {
            const eventItem = document.createElement('div');
            eventItem.className = 'event-item';
            
            const timestamp = new Date(event.timestamp);
            
            eventItem.innerHTML = `
                <div class="event-header">
                    <span class="status-badge ${event.status}">${event.status}</span>
                    <span class="event-timestamp">${timestamp.toLocaleString()}</span>
                </div>
                <div class="event-message">${escapeHtml(event.message || '')}</div>
            `;
            
            detailEvents.appendChild(eventItem);
        });
    } else {
        detailEvents.innerHTML = '<p>No events available</p>';
    }
    
    // Show the details section
    serviceDetailsSection.classList.remove('hidden');
}

// Close service details
function closeServiceDetails() {
    serviceDetailsSection.classList.add('hidden');
}

// Update last updated timestamp
function updateLastUpdated() {
    const now = new Date();
    lastUpdatedSpan.textContent = now.toLocaleString();
}

// Show error in the services list
function showError(message) {
    servicesList.innerHTML = `<div class="loading" style="color: var(--color-error);">Error: ${escapeHtml(message)}</div>`;
}

// Format time ago
function formatTimeAgo(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) {
        return `${diffInSeconds} seconds ago`;
    }
    
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    if (diffInMinutes < 60) {
        return `${diffInMinutes} minute${diffInMinutes !== 1 ? 's' : ''} ago`;
    }
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) {
        return `${diffInHours} hour${diffInHours !== 1 ? 's' : ''} ago`;
    }
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 30) {
        return `${diffInDays} day${diffInDays !== 1 ? 's' : ''} ago`;
    }
    
    // For older dates, just return the date string
    return date.toLocaleDateString();
}

// Escape HTML to prevent XSS
function escapeHtml(unsafe) {
    if (unsafe === null || unsafe === undefined) return '';
    return String(unsafe)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Start the application when DOM is loaded
document.addEventListener('DOMContentLoaded', init);