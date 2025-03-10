/**
 * LaneSwap Monitor - Main JavaScript
 * 
 * This file contains the core functionality for the LaneSwap web monitor dashboard.
 * It handles service data fetching, UI updates, and user interactions.
 */

// ===== STATE MANAGEMENT =====
const state = {
  services: {},
  refreshInterval: null,
  viewMode: 'grid',
  focusedServiceId: null,
  searchDebounceTimer: null,
  isSidebarExpanded: true
};

// ===== DOM ELEMENTS =====
const elements = {
  body: document.querySelector('.fusion-theme'),
  sidebar: document.querySelector('.sidebar'),
  sidebarToggle: document.getElementById('sidebarToggle'),
  apiUrlInput: document.getElementById('apiUrlInput'),
  connectBtn: document.getElementById('connectBtn'),
  refreshBtn: document.getElementById('refreshBtn'),
  refreshIntervalSelect: document.getElementById('refreshIntervalSelect'),
  viewGridBtn: document.getElementById('viewGridBtn'),
  viewTableBtn: document.getElementById('viewTableBtn'),
  servicesList: document.getElementById('servicesList'),
  searchInput: document.getElementById('searchInput'),
  clearSearchBtn: document.getElementById('clearSearchBtn'),
  lastUpdated: document.getElementById('lastUpdated'),
  themeSelect: document.getElementById('themeSelect'),
  themeToggleBtn: document.getElementById('themeToggleBtn'),
  dateFormatSelect: document.getElementById('dateFormatSelect'),
  saveSettingsBtn: document.getElementById('saveSettingsBtn'),
  toastContainer: document.getElementById('toastContainer')
};

// ===== LOCAL STORAGE HELPERS =====
/**
 * Get a value from localStorage with a default fallback
 * @param {string} key - The localStorage key
 * @param {*} defaultValue - Default value if key doesn't exist
 * @returns {*} The stored value or default
 */
const getStoredValue = (key, defaultValue) => {
  const value = localStorage.getItem(key);
  return value !== null ? value : defaultValue;
};

/**
 * Store a value in localStorage
 * @param {string} key - The localStorage key
 * @param {*} value - The value to store
 */
const storeValue = (key, value) => {
  localStorage.setItem(key, value);
};

// ===== INITIALIZATION =====
/**
 * Initialize the application
 */
function init() {
  // Load saved settings from localStorage
  elements.apiUrlInput.value = getStoredValue('laneswap-api-url', '');
  elements.refreshIntervalSelect.value = getStoredValue('laneswap-refresh-interval', '0');
  
  state.viewMode = getStoredValue('laneswap-view-mode', 'grid');
  updateViewMode();
  
  const savedTheme = getStoredValue('laneswap-theme', 'dark');
  elements.themeSelect.value = savedTheme;
  applyTheme(savedTheme);
  
  elements.dateFormatSelect.value = getStoredValue('laneswap-date-format', 'relative');
  
  // Initialize Bootstrap modals
  initializeModals();
  
  // Set up event listeners
  setupEventListeners();
  
  // Check for URL parameters
  handleUrlParameters();
  
  // Set the refresh interval
  setRefreshInterval();
  
  // Add window resize listener for responsive adjustments
  window.addEventListener('resize', handleResize);
  
  // Initialize sidebar state
  const savedSidebarState = localStorage.getItem('sidebar-expanded');
  state.isSidebarExpanded = savedSidebarState === null ? true : savedSidebarState === 'true';
  
  const appContainer = document.querySelector('.app-container');
  if (state.isSidebarExpanded) {
    appContainer.classList.add('sidebar-expanded');
  } else {
    appContainer.classList.add('sidebar-collapsed');
  }
}

/**
 * Initialize Bootstrap modals
 */
function initializeModals() {
  // Make sure Bootstrap is available
  if (typeof bootstrap === 'undefined') {
    console.error('Bootstrap is not loaded. Modals will not work properly.');
    return;
  }
  
  // Initialize all modals on the page
  const modalElements = document.querySelectorAll('.modal');
  modalElements.forEach(modalElement => {
    // Create a new Bootstrap modal instance for each modal
    new bootstrap.Modal(modalElement);
    
    // Prevent default anchor behavior for modal triggers
    const modalId = modalElement.id;
    const triggers = document.querySelectorAll(`[data-bs-target="#${modalId}"]`);
    
    triggers.forEach(trigger => {
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
        modal.show();
      });
    });
  });
  
  // Add event listeners for modal close buttons
  const closeButtons = document.querySelectorAll('[data-bs-dismiss="modal"]');
  closeButtons.forEach(button => {
    button.addEventListener('click', (e) => {
      e.preventDefault();
      const modalElement = button.closest('.modal');
      if (modalElement) {
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
          modal.hide();
        }
      }
    });
  });
}

/**
 * Set up all event listeners
 */
function setupEventListeners() {
  elements.connectBtn.addEventListener('click', fetchServices);
  elements.refreshBtn.addEventListener('click', fetchServices);
  elements.refreshIntervalSelect.addEventListener('change', setRefreshInterval);
  elements.viewGridBtn.addEventListener('click', () => setViewMode('grid'));
  elements.viewTableBtn.addEventListener('click', () => setViewMode('table'));
  elements.searchInput.addEventListener('input', debounceSearch);
  elements.clearSearchBtn.addEventListener('click', clearSearch);
  elements.saveSettingsBtn.addEventListener('click', saveSettings);
  elements.themeToggleBtn.addEventListener('click', toggleTheme);
  
  // Add event listener for the metrics refresh button
  const refreshMetricsBtn = document.getElementById('refreshMetricsBtn');
  if (refreshMetricsBtn) {
    refreshMetricsBtn.addEventListener('click', () => {
      fetchServices();
      showToast(getTranslation('metrics.refreshed') || 'Metrics refreshed', 'success');
    });
  }
  
  if (elements.sidebarToggle) {
    elements.sidebarToggle.addEventListener('click', toggleSidebar);
  }
  
  // Add direct event listeners for settings and help links
  const settingsLinks = document.querySelectorAll('[data-bs-target="#settingsModal"]');
  settingsLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      openSettingsModal();
    });
  });
  
  const helpLinks = document.querySelectorAll('[data-bs-target="#helpModal"]');
  helpLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      openHelpModal();
    });
  });
  
  // Close sidebar when clicking outside on mobile
  document.addEventListener('click', handleOutsideClick);
  
  // Sidebar toggle
  elements.sidebarToggle.addEventListener('click', toggleSidebar);
  document.querySelector('.sidebar-overlay')?.addEventListener('click', toggleSidebar);
}

/**
 * Handle clicks outside the sidebar (for mobile)
 * @param {Event} e - Click event
 */
function handleOutsideClick(e) {
  const screenWidth = window.innerWidth;
  if (screenWidth <= 768 && 
      elements.sidebar.classList.contains('open') && 
      !elements.sidebar.contains(e.target) && 
      e.target !== elements.sidebarToggle) {
    toggleSidebar();
  }
}

/**
 * Process URL parameters for API URL and service focus
 */
function handleUrlParameters() {
  const urlParams = new URLSearchParams(window.location.search);
  const apiParam = urlParams.get('api');
  const serviceParam = urlParams.get('service');
  
  if (apiParam) {
    elements.apiUrlInput.value = apiParam;
    
    // Store the service ID to focus on after loading
    if (serviceParam) {
      storeValue('laneswap-focus-service', serviceParam);
    }
    
    // Fetch services automatically
    fetchServices();
  }
}

/**
 * Handle window resize events
 */
function handleResize() {
  // Close sidebar on mobile when window is resized
  const screenWidth = window.innerWidth;
  if (screenWidth <= 768 && elements.sidebar.classList.contains('open')) {
    elements.sidebar.classList.remove('open');
  }
}

// ===== UI INTERACTIONS =====
/**
 * Toggle sidebar visibility
 */
function toggleSidebar() {
    const appContainer = document.querySelector('.app-container');
    
    if (appContainer.classList.contains('sidebar-expanded')) {
      appContainer.classList.remove('sidebar-expanded');
      appContainer.classList.add('sidebar-collapsed');
      state.isSidebarExpanded = false;
    } else {
      appContainer.classList.remove('sidebar-collapsed');
      appContainer.classList.add('sidebar-expanded');
      state.isSidebarExpanded = true;
    }
    
    // Store preference
    localStorage.setItem('sidebar-expanded', state.isSidebarExpanded);
  }

/**
 * Toggle between light and dark theme
 */
function toggleTheme() {
  const currentTheme = elements.body.getAttribute('data-theme') || 'dark';
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  
  applyTheme(newTheme);
  storeValue('laneswap-theme', newTheme);
  elements.themeSelect.value = newTheme;
  
  // Show toast notification
  showToast(`${newTheme.charAt(0).toUpperCase() + newTheme.slice(1)} mode activated`, 'success');
}

/**
 * Set the refresh interval for auto-updates
 */
function setRefreshInterval() {
  // Clear existing interval
  if (state.refreshInterval) {
    clearInterval(state.refreshInterval);
    state.refreshInterval = null;
  }
  
  // Get the selected interval
  const interval = parseInt(elements.refreshIntervalSelect.value, 10);
  
  // Save to localStorage
  storeValue('laneswap-refresh-interval', interval.toString());
  
  // Set new interval if not manual
  if (interval > 0) {
    state.refreshInterval = setInterval(fetchServices, interval * 1000);
    showToast(`Auto-refresh set to ${interval} seconds`, 'success');
  } else {
    showToast('Auto-refresh disabled', 'info');
  }
}

/**
 * Set the view mode (grid or table)
 * @param {string} mode - The view mode ('grid' or 'table')
 */
function setViewMode(mode) {
  state.viewMode = mode;
  storeValue('laneswap-view-mode', mode);
  updateViewMode();
  updateServicesUI();
  
  showToast(`View changed to ${mode} mode`, 'info');
}

/**
 * Update the view mode UI
 */
function updateViewMode() {
  if (state.viewMode === 'grid') {
    elements.viewGridBtn.classList.add('active');
    elements.viewTableBtn.classList.remove('active');
    elements.servicesList.classList.remove('view-table');
  } else {
    elements.viewTableBtn.classList.add('active');
    elements.viewGridBtn.classList.remove('active');
    elements.servicesList.classList.add('view-table');
  }
}

/**
 * Debounce the search input to prevent excessive UI updates
 */
function debounceSearch() {
  if (state.searchDebounceTimer) {
    clearTimeout(state.searchDebounceTimer);
  }
  
  state.searchDebounceTimer = setTimeout(() => {
    updateServicesUI();
    state.searchDebounceTimer = null;
  }, 300);
}

/**
 * Clear the search input
 */
function clearSearch() {
  elements.searchInput.value = '';
  updateServicesUI();
}

/**
 * Save user settings
 */
function saveSettings() {
  // Save theme
  const theme = elements.themeSelect.value;
  storeValue('laneswap-theme', theme);
  applyTheme(theme);
  
  // Save date format
  const dateFormat = elements.dateFormatSelect.value;
  storeValue('laneswap-date-format', dateFormat);
  
  // Close the modal
  const settingsModal = document.getElementById('settingsModal');
  if (settingsModal) {
    const modal = bootstrap.Modal.getOrCreateInstance(settingsModal);
    modal.hide();
  }
  
  // Update UI
  updateServicesUI();
  
  showToast('Settings saved successfully', 'success');
}

/**
 * Apply theme to the UI
 * @param {string} theme - The theme to apply ('light', 'dark', or 'system')
 */
function applyTheme(theme) {
  if (theme === 'system') {
    applySystemTheme();
  } else {
    applySpecificTheme(theme);
  }
}

/**
 * Apply system-preferred theme
 */
function applySystemTheme() {
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = prefersDark ? 'dark' : 'light';
  
  elements.body.setAttribute('data-theme', theme);
  updateThemeIcon(theme);
  
  // Listen for changes in system preference
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    if (elements.themeSelect.value === 'system') {
      const newTheme = e.matches ? 'dark' : 'light';
      elements.body.setAttribute('data-theme', newTheme);
      updateThemeIcon(newTheme);
    }
  });
}

/**
 * Apply a specific theme
 * @param {string} theme - The theme to apply ('light' or 'dark')
 */
function applySpecificTheme(theme) {
  elements.body.setAttribute('data-theme', theme);
  updateThemeIcon(theme);
}

/**
 * Update the theme toggle icon
 * @param {string} theme - The current theme
 */
function updateThemeIcon(theme) {
  if (elements.themeToggleBtn) {
    elements.themeToggleBtn.innerHTML = theme === 'dark' 
      ? '<span class="material-symbols-rounded">light_mode</span>' 
      : '<span class="material-symbols-rounded">dark_mode</span>';
  }
}

// ===== NOTIFICATIONS =====
/**
 * Show a toast notification
 * @param {string} message - The message to display
 * @param {string} type - The notification type ('info', 'success', 'warning', 'error')
 * @param {number} duration - How long to show the notification (ms)
 */
function showToast(message, type = 'info', duration = 3000) {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  const iconMap = {
    'info': 'info',
    'success': 'check_circle',
    'warning': 'warning',
    'error': 'error'
  };
  
  toast.innerHTML = `
    <span class="material-symbols-rounded toast-icon">${iconMap[type] || 'info'}</span>
    <span class="toast-message">${message}</span>
  `;
  
  elements.toastContainer.appendChild(toast);
  
  // Auto-remove toast after duration
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s forwards';
    setTimeout(() => {
      toast.remove();
    }, 300);
  }, duration);
}

// ===== DATE FORMATTING =====
/**
 * Format date based on user settings
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
  if (!dateString) return getTranslation('time.never');
  
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);
  
  const dateFormat = getStoredValue('laneswap-date-format', 'relative');
  
  if (dateFormat === 'absolute') {
    return date.toLocaleString();
  }
  
  // Relative time format
  const timeUnits = [
    { threshold: 5, key: 'time.now' },
    { threshold: 60, key: 'time.seconds', value: diffSec },
    { threshold: 120, key: 'time.minute', value: 1 },
    { threshold: 3600, key: 'time.minutes', value: diffMin },
    { threshold: 7200, key: 'time.hour', value: 1 },
    { threshold: 86400, key: 'time.hours', value: diffHour },
    { threshold: 172800, key: 'time.day', value: 1 },
    { threshold: Infinity, key: 'time.days', value: diffDay }
  ];
  
  const unit = timeUnits.find(unit => diffSec < unit.threshold);
  return unit.value ? `${unit.value} ${getTranslation(unit.key)}` : getTranslation(unit.key);
}

/**
 * Update the last updated timestamp
 */
function updateLastUpdated() {
  const now = new Date();
  const timeStr = now.toLocaleTimeString();
  elements.lastUpdated.textContent = `${getTranslation('lastUpdated').replace('Never', '')}: ${timeStr}`;
}

// ===== ERROR HANDLING =====
/**
 * Show error or empty state message
 * @param {string} message - The message to display
 * @param {boolean} isError - Whether this is an error state
 */
function showError(message, isError = true) {
  elements.servicesList.innerHTML = `
    <div class="${isError ? 'error-state' : 'empty-state'}">
      <span class="material-symbols-rounded ${isError ? 'error-icon' : 'empty-icon'}">
        ${isError ? 'error' : 'search_off'}
      </span>
      <p>${message}</p>
    </div>
  `;
  
  // Reset summary counts
  resetSummaryCounts();
  
  // Show error toast for error states
  if (isError) {
    showToast(message, 'error', 5000);
  }
}

/**
 * Reset all summary count elements to zero
 */
function resetSummaryCounts() {
  const countElements = ['healthyCount', 'warningCount', 'errorCount', 'staleCount', 'totalCount'];
  countElements.forEach(id => {
    document.getElementById(id).textContent = '0';
  });
}

// ===== SERVICE INTERACTIONS =====
/**
 * Focus on a specific service
 * @param {string} serviceId - The service ID to focus on
 */
function focusOnService(serviceId) {
  state.focusedServiceId = serviceId;
  
  // Scroll to the service card
  const serviceElement = document.getElementById(`service-${serviceId}`);
  if (serviceElement) {
    serviceElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    // Add focus animation
    serviceElement.classList.add('highlight-card');
    setTimeout(() => {
      serviceElement.classList.remove('highlight-card');
    }, 2000);
    
    // Show service details
    showServiceDetails(serviceId);
  }
}

/**
 * Show service details in modal
 * @param {string} serviceId - The service ID to show details for
 */
function showServiceDetails(serviceId) {
  const service = state.services[serviceId];
  if (!service) return;
  
  const modalElement = document.getElementById('serviceDetailsModal');
  if (!modalElement) {
    console.error('Service details modal element not found');
    return;
  }
  
  const modalBody = document.getElementById('serviceDetailsBody');
  const modalTitle = document.getElementById('serviceDetailsTitle');
  
  // Update modal title
  modalTitle.textContent = `${service.name} (${serviceId})`;
  
  // Format metadata as JSON with syntax highlighting
  const metadataHtml = formatMetadataHtml(service.metadata);
  
  // Format heartbeat history
  const heartbeatHistoryHtml = formatHeartbeatHistoryHtml(service.heartbeat_history);
  
  modalBody.innerHTML = `
    <div class="service-detail-grid">
      <div class="detail-section">
        <h3 class="detail-section-title">${getTranslation('service.details') || 'Details'}</h3>
        
        <div class="detail-row">
          <div class="detail-label">${getTranslation('service.id')}</div>
          <div class="detail-value">
            <code>${serviceId}</code>
          </div>
        </div>
        
        <div class="detail-row">
          <div class="detail-label">${getTranslation('service.name')}</div>
          <div class="detail-value">${service.name}</div>
        </div>
        
        <div class="detail-row">
          <div class="detail-label">${getTranslation('service.status')}</div>
          <div class="detail-value">
            <span class="status-chip ${service.status.toLowerCase()}">${service.status}</span>
          </div>
        </div>
        
        <div class="detail-row">
          <div class="detail-label">${getTranslation('service.lastHeartbeat')}</div>
          <div class="detail-value">
            <span class="material-symbols-rounded">schedule</span>
            ${formatDate(service.last_heartbeat)}
          </div>
        </div>
      </div>
      
      <div class="detail-section">
        <h3 class="detail-section-title">${getTranslation('service.message')}</h3>
        <p>${service.message || `<span class="no-data">${getTranslation('service.noMessage')}</span>`}</p>
        
        <h3 class="detail-section-title">${getTranslation('service.metadata')}</h3>
        ${metadataHtml}
      </div>
    </div>
    
    ${heartbeatHistoryHtml}
  `;
  
  // Make sure Bootstrap is available
  if (typeof bootstrap === 'undefined') {
    console.error('Bootstrap is not loaded. Modal will not work properly.');
    return;
  }
  
  try {
    // Show the modal using getOrCreateInstance
    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
    modal.show();
  } catch (error) {
    console.error('Error showing service details modal:', error);
  }
}

/**
 * Format service metadata as HTML
 * @param {Object} metadata - Service metadata
 * @returns {string} HTML representation of metadata
 */
function formatMetadataHtml(metadata) {
  if (!metadata || Object.keys(metadata).length === 0) {
    return `<p class="no-data">${getTranslation('service.noMetadata')}</p>`;
  }
  return `<pre class="metadata-json">${JSON.stringify(metadata, null, 2)}</pre>`;
}

/**
 * Format heartbeat history as HTML
 * @param {Array} history - Heartbeat history array
 * @returns {string} HTML representation of heartbeat history
 */
function formatHeartbeatHistoryHtml(history) {
  if (!history || history.length === 0) {
    return '';
  }
  
  return `
    <div class="detail-section">
      <h3 class="detail-section-title">${getTranslation('service.heartbeatHistory') || 'Heartbeat History'}</h3>
      <div class="service-table-container">
        <table class="service-table">
          <thead>
            <tr>
              <th>${getTranslation('service.timestamp') || 'Timestamp'}</th>
              <th>${getTranslation('service.status')}</th>
              <th>${getTranslation('service.message')}</th>
            </tr>
          </thead>
          <tbody>
            ${history.map(hb => `
              <tr>
                <td>${formatDate(hb.timestamp)}</td>
                <td>
                  <span class="status-chip ${hb.status.toLowerCase()}">${hb.status}</span>
                </td>
                <td>${hb.message || '-'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

// ===== DATA FETCHING =====
/**
 * Fetch services from the API
 */
async function fetchServices() {
  const apiUrl = elements.apiUrlInput.value.trim();
  
  if (!apiUrl) {
    showError('Please enter an API URL', false);
    return;
  }
  
  // Ensure the API URL has the correct format
  const formattedApiUrl = apiUrl.startsWith('http://') || apiUrl.startsWith('https://') 
    ? apiUrl 
    : `http://${apiUrl}`;
  
  // Show loading state
  elements.servicesList.innerHTML = `
    <div class="loading-state">
      <div class="pulse-loader">
        <div class="pulse-loader-inner"></div>
      </div>
      <p class="loading-text">${getTranslation('loading')}</p>
    </div>
  `;
  
  try {
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
      state.services = data.services;
      updateServicesUI();
      updateSummaryUI(data.summary);
      showToast('Services updated successfully', 'success');
    } else {
      console.error('Unexpected API response format:', data);
      showError(getTranslation('error'));
    }
    
    updateLastUpdated();
    
    // Check if we should focus on a specific service
    const focusServiceId = getStoredValue('laneswap-focus-service', null);
    if (focusServiceId && state.services[focusServiceId]) {
      setTimeout(() => focusOnService(focusServiceId), 100);
      // Clear the focus after showing it once
      localStorage.removeItem('laneswap-focus-service');
    }
    
    // Save API URL to localStorage
    storeValue('laneswap-api-url', apiUrl);
  } catch (error) {
    console.error('Fetch error:', error);
    showError(`${getTranslation('error')}: ${error.message}`);
  }
}

// ===== UI RENDERING =====
/**
 * Update the services UI based on the current view mode and search filter
 */
function updateServicesUI() {
  // Get search filter
  const searchFilter = elements.searchInput.value.toLowerCase();
  
  // Filter services based on search
  const filteredServices = Object.entries(state.services).filter(([id, service]) => {
    const searchString = `${id} ${service.name} ${service.status} ${service.message || ''}`.toLowerCase();
    return searchString.includes(searchFilter);
  });
  
  // Check if we have any services
  if (filteredServices.length === 0) {
    showError(getTranslation('noServices'), false);
    return;
  }
  
  // Sort services by status (error first, then warning, then stale, then healthy)
  const statusOrder = { 'error': 0, 'warning': 1, 'stale': 2, 'healthy': 3 };
  
  filteredServices.sort(([, a], [, b]) => {
    return (statusOrder[a.status.toLowerCase()] || 4) - (statusOrder[b.status.toLowerCase()] || 4);
  });
  
  // Render services based on view mode
  if (state.viewMode === 'grid') {
    renderGridView(filteredServices);
  } else {
    renderTableView(filteredServices);
  }
}

/**
 * Render services in grid view
 * @param {Array} filteredServices - Array of filtered service entries
 */
function renderGridView(filteredServices) {
  elements.servicesList.innerHTML = filteredServices.map(([id, service]) => `
    <div class="service-card" id="service-${id}" onclick="showServiceDetails('${id}')">
      <div class="service-header">
        <h3 class="service-title">${service.name}</h3>
        <div class="service-status ${service.status.toLowerCase()}">${service.status}</div>
      </div>
      <div class="service-body">
        <div class="service-id">${id}</div>
        <div class="service-message">${service.message || getTranslation('service.noMessage')}</div>
        <div class="service-footer">
          <div class="service-time">
            <span class="material-symbols-rounded">schedule</span>
            ${formatDate(service.last_heartbeat)}
          </div>
        </div>
      </div>
    </div>
  `).join('');
}

/**
 * Render services in table view
 * @param {Array} filteredServices - Array of filtered service entries
 */
function renderTableView(filteredServices) {
  elements.servicesList.innerHTML = `
    <div class="service-table-container">
      <table class="service-table">
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
              <td><span class="status-chip ${service.status.toLowerCase()}">${service.status}</span></td>
              <td>${service.message || '-'}</td>
              <td>${formatDate(service.last_heartbeat)}</td>
              <td class="service-id">${id}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

/**
 * Update the summary UI
 * @param {Object} summary - Summary data object
 */
function updateSummaryUI(summary) {
  if (!summary) return;
  
  // Get the counts
  const healthyCount = summary.healthy || 0;
  const warningCount = summary.warning || 0;
  const errorCount = summary.error || 0;
  const staleCount = summary.stale || 0;
  const totalCount = summary.total || 0;
  
  // Update count elements
  document.getElementById('healthyCount').textContent = healthyCount;
  document.getElementById('warningCount').textContent = warningCount;
  document.getElementById('errorCount').textContent = errorCount;
  document.getElementById('staleCount').textContent = staleCount;
  document.getElementById('totalCount').textContent = totalCount;
  
  // Calculate percentages
  if (totalCount > 0) {
    const healthyPercentage = Math.round((healthyCount / totalCount) * 100);
    const warningPercentage = Math.round((warningCount / totalCount) * 100);
    const errorPercentage = Math.round((errorCount / totalCount) * 100);
    const stalePercentage = Math.round((staleCount / totalCount) * 100);
    
    // Update percentage displays
    document.getElementById('healthyPercentage').textContent = `${healthyPercentage}%`;
    document.getElementById('warningPercentage').textContent = `${warningPercentage}%`;
    document.getElementById('errorPercentage').textContent = `${errorPercentage}%`;
    document.getElementById('stalePercentage').textContent = `${stalePercentage}%`;
    
    // Update progress bars
    document.getElementById('healthyProgress').style.width = `${healthyPercentage}%`;
    document.getElementById('warningProgress').style.width = `${warningPercentage}%`;
    document.getElementById('errorProgress').style.width = `${errorPercentage}%`;
    document.getElementById('staleProgress').style.width = `${stalePercentage}%`;
    
    // Calculate and display uptime if available
    if (summary.uptime) {
      document.getElementById('uptimeValue').textContent = formatUptime(summary.uptime);
    } else {
      // If no uptime data, estimate based on healthy percentage
      const uptimeEstimate = healthyPercentage;
      document.getElementById('uptimeValue').textContent = `~${uptimeEstimate}% ${getTranslation('summary.estimatedUptime') || 'estimated'}`;
    }
  } else {
    // Reset percentages and progress bars if no services
    const percentageElements = ['healthyPercentage', 'warningPercentage', 'errorPercentage', 'stalePercentage'];
    const progressElements = ['healthyProgress', 'warningProgress', 'errorProgress', 'staleProgress'];
    
    percentageElements.forEach(id => {
      document.getElementById(id).textContent = '0%';
    });
    
    progressElements.forEach(id => {
      document.getElementById(id).style.width = '0%';
    });
    
    document.getElementById('uptimeValue').textContent = '-';
  }
}

/**
 * Format uptime value into a readable string
 * @param {number} uptime - Uptime value in seconds or as a percentage
 * @returns {string} Formatted uptime string
 */
function formatUptime(uptime) {
  // If uptime is already a percentage string
  if (typeof uptime === 'string' && uptime.includes('%')) {
    return uptime;
  }
  
  // If uptime is a percentage number
  if (uptime >= 0 && uptime <= 100) {
    return `${uptime}%`;
  }
  
  // If uptime is in seconds, convert to a readable format
  const days = Math.floor(uptime / 86400);
  const hours = Math.floor((uptime % 86400) / 3600);
  const minutes = Math.floor((uptime % 3600) / 60);
  
  if (days > 0) {
    return `${days}d ${hours}h`;
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else {
    return `${minutes}m`;
  }
}

/**
 * Open the settings modal
 */
function openSettingsModal() {
  const modalElement = document.getElementById('settingsModal');
  if (!modalElement) {
    console.error('Settings modal element not found');
    return;
  }
  
  // Make sure Bootstrap is available
  if (typeof bootstrap === 'undefined') {
    console.error('Bootstrap is not loaded. Modal will not work properly.');
    return;
  }
  
  try {
    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
    modal.show();
  } catch (error) {
    console.error('Error showing settings modal:', error);
  }
}

/**
 * Open the help modal
 */
function openHelpModal() {
  const modalElement = document.getElementById('helpModal');
  if (!modalElement) {
    console.error('Help modal element not found');
    return;
  }
  
  // Make sure Bootstrap is available
  if (typeof bootstrap === 'undefined') {
    console.error('Bootstrap is not loaded. Modal will not work properly.');
    return;
  }
  
  try {
    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
    modal.show();
  } catch (error) {
    console.error('Error showing help modal:', error);
  }
}

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', init);