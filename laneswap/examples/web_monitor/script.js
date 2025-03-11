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
  isSidebarExpanded: true,
  currentLanguage: 'en',
  notificationsEnabled: false
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
  toastContainer: document.getElementById('toastContainer'),
  notificationToggleBtn: document.getElementById('notificationToggleBtn')
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
  // Ensure required DOM elements exist
  ensureRequiredElements();
  
  // Load saved settings from localStorage
  elements.apiUrlInput.value = getStoredValue('laneswap-api-url', '');
  elements.refreshIntervalSelect.value = getStoredValue('laneswap-refresh-interval', '0');
  
  // Initialize notification state
  initializeNotifications();
  
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
  
  // Initialize language and enhanced monitoring after DOM is fully loaded
  document.addEventListener('DOMContentLoaded', () => {
    initializeLanguage();
    // Add enhanced monitoring features after DOM is fully loaded
    setTimeout(() => {
      try {
        addEnhancedMonitoring();
      } catch (error) {
        console.warn('Error adding enhanced monitoring:', error);
      }
    }, 100);
  });
  
  // Initialize theme
  initializeTheme();
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
  elements.notificationToggleBtn.addEventListener('click', toggleNotifications);
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
    link.addEventListener('click', openSettingsModal);
  });
  
  const helpLinks = document.querySelectorAll('[data-bs-target="#helpModal"]');
  helpLinks.forEach(link => {
    link.addEventListener('click', openHelpModal);
  });
  
  // Add click handler for outside sidebar clicks (mobile)
  document.querySelector('.sidebar-overlay').addEventListener('click', handleOutsideClick);
  
  // Add keyboard shortcut for refresh (F5)
  document.addEventListener('keydown', (e) => {
    if (e.key === 'F5') {
      e.preventDefault();
      fetchServices();
    }
  });
}

/**
 * Handle clicks outside the sidebar (for mobile)
 * @param {Event} e - Click event
 */
function handleOutsideClick(e) {
  const screenWidth = window.innerWidth;
  if (screenWidth <= 768 && 
      document.querySelector('.app-container').classList.contains('sidebar-expanded') && 
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
  const screenWidth = window.innerWidth;
  const appContainer = document.querySelector('.app-container');
  
  // Close sidebar on mobile when window is resized
  if (screenWidth <= 768 && appContainer.classList.contains('sidebar-expanded')) {
    toggleSidebar();
  }
  
  // Reset sidebar on desktop
  if (screenWidth > 768) {
    appContainer.classList.remove('sidebar-collapsed');
    appContainer.classList.add('sidebar-expanded');
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
  
  // Store preference (only on desktop)
  if (window.innerWidth > 768) {
    localStorage.setItem('sidebar-expanded', state.isSidebarExpanded);
  }
}

/**
 * Toggle between light and dark themes
 */
function toggleTheme() {
  // Get current theme
  const currentTheme = document.body.getAttribute('data-theme') || 'light';
  
  // Toggle to the opposite theme
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  
  // Apply the new theme
  applyTheme(newTheme);
  
  // Update the theme select dropdown if it exists
  if (elements.themeSelect) {
    elements.themeSelect.value = newTheme;
  }
  
  // Save the preference
  storeValue('laneswap-theme', newTheme);
  
  // Show feedback
  showToast(`Theme changed to ${newTheme} mode`, 'success', 3000, true);
}

/**
 * Apply a specific theme to the application
 * @param {string} theme - The theme to apply ('light' or 'dark')
 */
function applyTheme(theme) {
  // Validate theme
  const validTheme = ['light', 'dark'].includes(theme) ? theme : 'dark';
  
  // Apply to body
  document.body.setAttribute('data-theme', validTheme);
  
  // Apply to root element for CSS variables
  document.documentElement.setAttribute('data-theme', validTheme);
  
  // Update theme toggle button icon
  const themeIcon = document.querySelector('.theme-toggle .material-symbols-rounded');
  if (themeIcon) {
    themeIcon.textContent = validTheme === 'dark' ? 'light_mode' : 'dark_mode';
  }
  
  // Update any other theme-specific elements
  const appContainer = document.querySelector('.app-container');
  if (appContainer) {
    appContainer.classList.toggle('theme-dark', validTheme === 'dark');
    appContainer.classList.toggle('theme-light', validTheme === 'light');
  }
  
  // Update meta theme-color for mobile browsers
  const metaThemeColor = document.querySelector('meta[name="theme-color"]');
  if (metaThemeColor) {
    metaThemeColor.setAttribute('content', 
      validTheme === 'dark' ? '#1a1a1a' : '#ffffff');
  }
}

/**
 * Set up event listeners for the theme toggle button
 */
function setupThemeToggle() {
  const themeToggleBtn = document.querySelector('.theme-toggle');
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', toggleTheme);
  }
  
  // Also set up the theme select dropdown if it exists
  if (elements.themeSelect) {
    elements.themeSelect.addEventListener('change', (e) => {
      applyTheme(e.target.value);
      storeValue('laneswap-theme', e.target.value);
    });
  }
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
    showToast(`Auto-refresh set to ${interval} seconds`, 'success', 3000, true);
  } else {
    showToast('Auto-refresh disabled', 'info', 3000, true);
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
 * Update the view mode (grid or table)
 */
function updateViewMode() {
  // Ensure the services container exists
  ensureRequiredElements();
  
  if (!elements.servicesList) {
    console.error('Services container element still not found after attempting to create it');
    return;
  }
  
  // Update UI to reflect current view mode
  if (state.viewMode === 'grid') {
    elements.viewGridBtn.classList.add('active');
    elements.viewTableBtn.classList.remove('active');
    elements.servicesList.classList.add('grid-view');
    elements.servicesList.classList.remove('table-view');
  } else {
    elements.viewGridBtn.classList.remove('active');
    elements.viewTableBtn.classList.add('active');
    elements.servicesList.classList.remove('grid-view');
    elements.servicesList.classList.add('table-view');
  }
  
  // Re-render services if we have any
  if (Object.keys(state.services).length > 0) {
    renderServices();
  }
  
  // Store preference
  storeValue('laneswap-view-mode', state.viewMode);
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
  
  showToast('Settings saved successfully', 'success', 3000, true);
}

// ===== NOTIFICATIONS =====
/**
 * Show a toast notification
 * @param {string} message - The message to display
 * @param {string} type - The type of toast (success, error, warning, info)
 * @param {number} duration - How long to show the toast in ms
 * @param {boolean} forceShow - Whether to show the toast even if notifications are disabled
 */
function showToast(message, type = 'info', duration = 3000, forceShow = false) {
  // Don't show toast if notifications are disabled, unless forceShow is true
  if (!state.notificationsEnabled && !forceShow) return;

  const toastContainer = document.getElementById('toastContainer');
  if (!toastContainer) return;
  
  // Create toast element
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  // Get appropriate icon based on type
  let icon = 'info';
  switch (type) {
    case 'success': icon = 'check_circle'; break;
    case 'error': icon = 'error'; break;
    case 'warning': icon = 'warning'; break;
  }
  
  // Set toast content
  toast.innerHTML = `
    <div class="toast-header">
      <span class="toast-icon material-symbols-rounded">${icon}</span>
      <h5 class="toast-title">${type.charAt(0).toUpperCase() + type.slice(1)}</h5>
      <button class="toast-close" onclick="this.parentElement.parentElement.remove()">
        <span class="material-symbols-rounded">close</span>
      </button>
    </div>
    <div class="toast-body">${message}</div>
  `;
  
  // Add toast to container
  toastContainer.appendChild(toast);
  
  // Trigger animation
  setTimeout(() => {
    toast.classList.add('show');
  }, 10);
  
  // Auto-remove after duration
  if (duration > 0) {
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => {
        toast.remove();
      }, 300);
    }, duration);
  }
}

/**
 * Add loading indicators to buttons
 */
function setButtonLoading(button, isLoading) {
  if (!button) return;
  
  if (isLoading) {
    const originalText = button.innerHTML;
    button.setAttribute('data-original-text', originalText);
    button.innerHTML = `
      <span class="loading-indicator"></span>
      <span class="ms-2">Loading...</span>
    `;
    button.disabled = true;
  } else {
    const originalText = button.getAttribute('data-original-text');
    if (originalText) {
      button.innerHTML = originalText;
    }
    button.disabled = false;
  }
}

/**
 * Add tooltips to elements
 */
function initializeTooltips() {
  const tooltipElements = document.querySelectorAll('[data-tooltip]');
  
  tooltipElements.forEach(element => {
    const tooltipText = element.getAttribute('data-tooltip');
    
    // Create tooltip container
    const tooltip = document.createElement('span');
    tooltip.className = 'tooltip-text';
    tooltip.textContent = tooltipText;
    
    // Add tooltip to element
    element.classList.add('tooltip');
    element.appendChild(tooltip);
  });
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
  if (elements.servicesList) {
    elements.servicesList.innerHTML = `
      <div class="${isError ? 'error-state' : 'empty-state'}">
        <span class="material-symbols-rounded ${isError ? 'error-icon' : 'empty-icon'}">
          ${isError ? 'error' : 'search_off'}
        </span>
        <p>${message}</p>
      </div>
    `;
  }
  
  // Reset summary counts - safely
  try {
    resetSummaryCounts();
  } catch (error) {
    console.warn('Error resetting summary counts:', error);
  }
  
  // Show error toast for error states
  if (isError) {
    showToast(message, 'error', 5000, true); // Force show error toasts
  }
}

/**
 * Reset all summary count elements to zero
 */
function resetSummaryCounts() {
  const countElements = ['healthyCount', 'warningCount', 'errorCount', 'staleCount', 'totalCount'];
  countElements.forEach(id => {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = '0';
    }
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
 * @param {string} serviceId - The ID of the service to show details for
 */
function showServiceDetails(serviceId) {
  const service = state.services[serviceId];
  if (!service) return;
  
  const modalTitle = document.getElementById('serviceDetailsTitle');
  const modalBody = document.getElementById('serviceDetailsBody');
  
  if (!modalTitle || !modalBody) return;
  
  // Set modal title
  modalTitle.textContent = service.name || service.id;
  
  // Format the service details
  const statusClass = service.status.toLowerCase();
  const formattedTime = formatTime(service.last_heartbeat);
  
  // Create modal content
  modalBody.innerHTML = `
    <div class="service-detail-grid mb-4">
      <div class="detail-card">
        <div class="detail-title">Service ID</div>
        <div class="detail-value monospace">${service.id}</div>
      </div>
      <div class="detail-card">
        <div class="detail-title">Status</div>
        <div class="detail-value">
          <span class="status-chip ${statusClass}">${service.status}</span>
        </div>
      </div>
      <div class="detail-card">
        <div class="detail-title">Last Heartbeat</div>
        <div class="detail-value">${formattedTime}</div>
      </div>
      <div class="detail-card">
        <div class="detail-title">Message</div>
        <div class="detail-value">${service.last_message || 'No message'}</div>
      </div>
    </div>
    
    <h6 class="mb-3">Recent Events</h6>
    <div class="timeline">
      ${renderSimpleTimeline(service.events)}
    </div>
    
    <h6 class="mb-3 mt-4">Service Logs</h6>
    <div class="service-logs">
      ${renderServiceLogs(service.events)}
    </div>
  `;
  
  // Show the modal
  const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('serviceDetailsModal'));
  modal.show();
}

/**
 * Render a simple timeline with proper styling
 * @param {Array} events - Array of events to render
 * @returns {string} HTML for the timeline
 */
function renderSimpleTimeline(events) {
  if (!events || events.length === 0) {
    return '<div class="text-center py-3">No events recorded</div>';
  }
  
  // Sort events by timestamp (newest first)
  const sortedEvents = [...events].sort((a, b) => {
    return new Date(b.timestamp) - new Date(a.timestamp);
  });
  
  // Take only the last 10 events
  const recentEvents = sortedEvents.slice(0, 10);
  
  return recentEvents.map(event => {
    const statusClass = event.status.toLowerCase();
    const time = formatTime(event.timestamp);
    
    return `
      <div class="timeline-item ${statusClass}">
        <div class="timeline-dot ${statusClass}"></div>
        <div class="timeline-time">${time}</div>
        <div class="timeline-content">
          <span class="timeline-status ${statusClass}">${event.status}</span>
          <span class="timeline-message">${event.message || 'No message'}</span>
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Render service logs with focus on errors and diagnostics
 */
function renderServiceLogs(events) {
  if (!events || events.length === 0) {
    return '<div class="text-center py-3">No logs available</div>';
  }
  
  // Sort and filter error events
  const sortedEvents = [...events].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  const errorEvents = sortedEvents.filter(event => 
    event.status.toLowerCase() === 'error' || 
    event.message?.toLowerCase().includes('error') ||
    event.message?.toLowerCase().includes('exception') ||
    event.message?.toLowerCase().includes('fail')
  );
  
  // If no errors, show healthy status
  if (errorEvents.length === 0) {
    return `
      <div class="logs-container">
        <div class="log-summary healthy">
          <span class="material-symbols-rounded">check_circle</span>
          <div>
            <h6>System Healthy</h6>
            <p>No errors detected in the last ${sortedEvents.length} events</p>
          </div>
        </div>
      </div>
    `;
  }
  
  // Group errors by type
  const errorTypes = {};
  errorEvents.forEach(event => {
    let errorType = categorizeError(event.message);
    if (!errorTypes[errorType]) {
      errorTypes[errorType] = [];
    }
    errorTypes[errorType].push(event);
  });
  
  // Generate error overview
  const overview = generateErrorOverview(errorTypes, errorEvents);
  
  // Generate detailed error groups
  const errorGroups = Object.entries(errorTypes).map(([errorType, events]) => {
    const count = events.length;
    const latestEvent = events[0];
    const time = new Date(latestEvent.timestamp).toLocaleTimeString();
    const groupId = `error-group-${btoa(errorType).replace(/[^a-zA-Z0-9]/g, '')}`;
    
    return `
      <div class="error-group">
        <div class="error-group-header" onclick="toggleErrorGroup('${groupId}')">
          ${renderErrorGroupHeader(errorType, count, time)}
        </div>
        <div id="${groupId}" class="error-group-content" style="display: none;">
          ${events.map(renderErrorDetail).join('')}
        </div>
      </div>
    `;
  }).join('');

  return `
    <div class="logs-container error-logs-container">
      ${overview}
      <div class="error-groups">
        ${errorGroups}
      </div>
    </div>
  `;
}

/**
 * Generate error overview section
 */
function generateErrorOverview(errorTypes, allErrors) {
  const totalErrors = allErrors.length;
  const uniqueTypes = Object.keys(errorTypes).length;
  const latestError = allErrors[0];
  const oldestError = allErrors[allErrors.length - 1];
  const timeSpan = Math.round((new Date(latestError.timestamp) - new Date(oldestError.timestamp)) / 1000 / 60);
  
  // Calculate frequency
  const errorsPerMinute = (totalErrors / timeSpan).toFixed(2);
  
  // Find most frequent error type
  let mostFrequentType = '';
  let maxCount = 0;
  Object.entries(errorTypes).forEach(([type, events]) => {
    if (events.length > maxCount) {
      maxCount = events.length;
      mostFrequentType = type;
    }
  });

  return `
    <div class="error-overview">
      <div class="overview-header">
        <span class="material-symbols-rounded">warning</span>
        <h6>Error Overview</h6>
      </div>
      <div class="overview-stats">
        <div class="stat-item">
          <div class="stat-value">${totalErrors}</div>
          <div class="stat-label">Total Errors</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">${uniqueTypes}</div>
          <div class="stat-label">Error Types</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">${errorsPerMinute}</div>
          <div class="stat-label">Errors/min</div>
        </div>
      </div>
      <div class="overview-details">
        <div class="detail-item">
          <span class="material-symbols-rounded">error</span>
          <span>Most frequent: ${mostFrequentType} (${maxCount}x)</span>
        </div>
        <div class="detail-item">
          <span class="material-symbols-rounded">schedule</span>
          <span>Latest: ${new Date(latestError.timestamp).toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  `;
}

/**
 * Toggle visibility of error group content
 * @param {string} groupId - ID of the error group to toggle
 */
function toggleErrorGroup(groupId) {
  const content = document.getElementById(groupId);
  const header = content.previousElementSibling;
  const icon = header.querySelector('.material-symbols-rounded');
  
  if (content.style.display === 'none') {
    content.style.display = 'block';
    header.classList.add('expanded');
  } else {
    content.style.display = 'none';
    header.classList.remove('expanded');
  }
}

/**
 * Render error group header
 */
function renderErrorGroupHeader(errorType, count, latestTime) {
  return `
    <div class="error-type">
      <span class="material-symbols-rounded">error</span>
      <span>${errorType}</span>
    </div>
    <div class="error-meta">
      <span class="error-time">${latestTime}</span>
      <span class="error-count">${count}</span>
    </div>
  `;
}

/**
 * Toggle visibility of error stack trace
 * @param {HTMLElement} element - The header element that was clicked
 */
function toggleErrorStack(element) {
  const container = element.closest('.error-stack-container');
  const stack = container.querySelector('.error-stack');
  const icon = element.querySelector('.material-symbols-rounded');
  
  if (stack.style.display === 'none' || !stack.style.display) {
    stack.style.display = 'block';
    element.classList.add('expanded');
    icon.textContent = 'expand_less';
  } else {
    stack.style.display = 'none';
    element.classList.remove('expanded');
    icon.textContent = 'code';
  }
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
      // Track status changes for notifications
      if (state.services) {
        // Check for status changes in existing services
        Object.entries(data.services).forEach(([id, service]) => {
          const existingService = state.services[id];
          if (existingService && existingService.status !== service.status) {
            // Service status has changed, trigger notification
            showServiceNotification(service, existingService.status.toLowerCase());
          }
        });
      }
      
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
 * Update the services UI based on the current search filter
 */
function updateServicesUI() {
  try {
    // Get search filter
    const searchFilter = elements.searchInput.value.toLowerCase();
    
    // Filter services based on search
    const filteredServices = Object.entries(state.services || {}).filter(([id, service]) => {
      const searchString = `${id} ${service.name} ${service.status} ${service.message || ''}`.toLowerCase();
      return searchString.includes(searchFilter);
    });
    
    // If no services found after filtering
    if (filteredServices.length === 0) {
      if (searchFilter) {
        // No results for search
        showError(getTranslation('noSearchResults'), false);
      } else {
        // No services at all
        showError(getTranslation('noServices'), false);
      }
      return;
    }
    
    // Sort services by status (error first, then warning, then stale, then healthy)
    const statusOrder = { 'error': 0, 'warning': 1, 'stale': 2, 'healthy': 3 };
    
    filteredServices.sort(([, a], [, b]) => {
      return (statusOrder[a.status.toLowerCase()] || 4) - (statusOrder[b.status.toLowerCase()] || 4);
    });
    
    // Render services in grid view
    renderGridView(filteredServices);
  } catch (error) {
    console.error('Error updating services UI:', error);
    showError(`${getTranslation('error')}: ${error.message}`);
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
 * Update the summary UI with service statistics
 * @param {Object} stats - Service statistics object
 */
function updateSummaryUI(stats) {
  try {
    // Default values if stats is undefined
    const data = stats || { 
      healthy: 0, 
      warning: 0, 
      error: 0, 
      stale: 0, 
      total: 0,
      healthyPercentage: 0,
      warningPercentage: 0,
      errorPercentage: 0,
      stalePercentage: 0
    };
    
    // Update count elements
    const healthyCountElement = document.getElementById('healthyCount');
    const warningCountElement = document.getElementById('warningCount');
    const errorCountElement = document.getElementById('errorCount');
    const staleCountElement = document.getElementById('staleCount');
    
    // Safely update elements if they exist
    if (healthyCountElement) healthyCountElement.textContent = data.healthy;
    if (warningCountElement) warningCountElement.textContent = data.warning;
    if (errorCountElement) errorCountElement.textContent = data.error;
    if (staleCountElement) staleCountElement.textContent = data.stale;
    
    // Update the document title to show current status
    updateDocumentTitle(data);
  } catch (error) {
    console.error('Error updating summary UI:', error);
  }
}

/**
 * Update document title to reflect current status
 * @param {Object} stats - Service statistics object
 */
function updateDocumentTitle(stats) {
  if (!stats) return;
  
  let prefix = '';
  
  // Add status indicator to title
  if (stats.error > 0) {
    prefix = '🔴 ';
  } else if (stats.warning > 0) {
    prefix = '🟠 ';
  } else if (stats.stale > 0) {
    prefix = '⚪ ';
  } else if (stats.healthy > 0) {
    prefix = '🟢 ';
  }
  
  // Get base title
  const baseTitle = translations[state.currentLanguage].title || 'LaneSwap Monitor';
  
  // Update document title
  document.title = `${prefix}${baseTitle}`;
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

/**
 * Change the application language
 * @param {string} lang - Language code ('en' or 'th')
 */
function changeLanguage(lang) {
  if (!['en', 'th'].includes(lang)) return;

  // Update state
  state.currentLanguage = lang;
  
  // Get UI elements
  const languageSwitcher = document.querySelector('.language-switcher');
  const langButtons = document.querySelectorAll('.lang-btn');
  
  // Update buttons
  langButtons.forEach(btn => {
    const isActive = btn.dataset.lang === lang;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-pressed', isActive);
  });
  
  // Move indicator
  languageSwitcher.setAttribute('data-active', lang);
  
  // Store preference
  localStorage.setItem('laneswap-language', lang);
  
  try {
    // Update translations using the global function
    if (typeof window.updateTranslations === 'function') {
      window.updateTranslations(lang);
    } else {
      console.error('updateTranslations function not found');
    }
    
    // Show feedback
    showToast(`Language changed to ${lang.toUpperCase()}`, 'success');
  } catch (error) {
    console.error('Error updating translations:', error);
    showToast('Error changing language', 'error');
  }
}

/**
 * Initialize language preference
 */
function initializeLanguage() {
  try {
    // Get saved language preference or default to 'en'
    const savedLang = localStorage.getItem('laneswap-language') || 'en';
    
    // Validate saved language
    const lang = ['en', 'th'].includes(savedLang) ? savedLang : 'en';
    
    // Update state
    state.currentLanguage = lang;
    
    // Get UI elements
    const languageSwitcher = document.querySelector('.language-switcher');
    const langButtons = document.querySelectorAll('.lang-btn');
    
    // Set initial button states
    langButtons.forEach(btn => {
      const isActive = btn.dataset.lang === lang;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-pressed', isActive);
    });
    
    // Set initial indicator position
    languageSwitcher.setAttribute('data-active', lang);
    
    // Set initial translations
    updateTranslations(lang);
  } catch (error) {
    console.error('Error initializing language:', error);
    // Set fallback to English
    state.currentLanguage = 'en';
  }
}

/**
 * Format a timestamp in a human-readable way
 * @param {string|Date} timestamp - The timestamp to format
 * @returns {string} Formatted time string
 */
function formatTime(timestamp) {
  if (!timestamp) return 'Never';
  
  try {
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) return 'Invalid date';
    
    // Get date format preference
    const format = localStorage.getItem('laneswap-date-format') || 'relative';
    
    if (format === 'relative') {
      return getRelativeTimeString(date);
    } else {
      return date.toLocaleString();
    }
  } catch (error) {
    console.error('Error formatting time:', error);
    return 'Error';
  }
}

/**
 * Get a relative time string (e.g., "2 hours ago")
 * @param {Date} date - The date to format
 * @returns {string} Relative time string
 */
function getRelativeTimeString(date) {
  const now = new Date();
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);
  
  if (diffSec < 60) {
    return `${diffSec} second${diffSec !== 1 ? 's' : ''} ago`;
  } else if (diffMin < 60) {
    return `${diffMin} minute${diffMin !== 1 ? 's' : ''} ago`;
  } else if (diffHour < 24) {
    return `${diffHour} hour${diffHour !== 1 ? 's' : ''} ago`;
  } else {
    return `${diffDay} day${diffDay !== 1 ? 's' : ''} ago`;
  }
}

/**
 * Render the footer with GitHub link
 */
function renderFooter() {
  const footer = document.querySelector('.footer');
  if (!footer) return;
  
  const lastUpdatedTime = new Date().toLocaleTimeString();
  
  footer.innerHTML = `
    <div class="footer-left">
      <span>Last updated: ${lastUpdatedTime}</span>
    </div>
    <a href="https://github.com/yourusername/laneswap" target="_blank" class="github-link">
      <span class="material-symbols-rounded github-icon">code</span>
      <span>LaneSwap</span>
    </a>
  `;
}

/**
 * Update the header to include refresh button
 */
function updateHeader() {
  const header = document.querySelector('.header');
  if (!header) return;
  
  // Create header actions container if it doesn't exist
  let headerActions = header.querySelector('.header-actions');
  if (!headerActions) {
    headerActions = document.createElement('div');
    headerActions.className = 'header-actions';
    header.appendChild(headerActions);
  }
  
  // Add refresh button to header actions
  headerActions.innerHTML = `
    <button id="refreshBtn" class="refresh-button" title="Refresh data">
      <span class="material-symbols-rounded">refresh</span>
    </button>
    ${headerActions.innerHTML}
  `;
  
  // Update elements reference
  elements.refreshBtn = document.getElementById('refreshBtn');
  
  // Add event listener to refresh button
  if (elements.refreshBtn) {
    elements.refreshBtn.addEventListener('click', () => {
      fetchServices();
    });
  }
}

/**
 * Update last updated time in footer
 */
function updateLastUpdatedTime() {
  const lastUpdatedTime = new Date().toLocaleTimeString();
  const footerLeft = document.querySelector('.footer-left');
  
  if (footerLeft) {
    footerLeft.innerHTML = `<span>Last updated: ${lastUpdatedTime}</span>`;
  }
}

/**
 * Categorize error message into a specific type
 * @param {string} message - The error message to categorize
 * @returns {string} The categorized error type
 */
function categorizeError(message) {
  if (!message) return 'Unknown Error';
  
  const messageLower = message.toLowerCase();
  
  // Common error patterns
  const errorMatch = message.match(/Error: ([^:]+)/) || 
                    message.match(/Exception: ([^:]+)/) ||
                    message.match(/^([^:]+Error)/);
  
  if (errorMatch && errorMatch[1]) {
    return errorMatch[1].trim();
  }
  
  // Check for common error keywords
  if (messageLower.includes('timeout')) {
    return 'Timeout Error';
  }
  if (messageLower.includes('connection')) {
    return 'Connection Error';
  }
  if (messageLower.includes('memory')) {
    return 'Memory Error';
  }
  if (messageLower.includes('authentication') || messageLower.includes('auth')) {
    return 'Authentication Error';
  }
  if (messageLower.includes('permission') || messageLower.includes('access')) {
    return 'Permission Error';
  }
  if (messageLower.includes('not found') || messageLower.includes('404')) {
    return 'Not Found Error';
  }
  if (messageLower.includes('validation')) {
    return 'Validation Error';
  }
  if (messageLower.includes('database') || messageLower.includes('db')) {
    return 'Database Error';
  }
  
  // If no specific pattern matches, use first part of message
  return message.substring(0, 30) + (message.length > 30 ? '...' : '');
}

/**
 * Render an individual error detail
 * @param {Object} event - The error event to render
 * @returns {string} HTML for the error detail
 */
function renderErrorDetail(event) {
  return `
    <div class="error-details">
      <div class="error-time">Time: ${new Date(event.timestamp).toLocaleTimeString()}</div>
      <div class="error-message">${event.message}</div>
      ${event.error_details ? `
        <div class="error-stack-container">
          <div class="error-stack-header" onclick="event.stopPropagation(); toggleErrorStack(this)">
            <span class="material-symbols-rounded">code</span>
            <span>Stack Trace</span>
          </div>
          <pre class="error-stack">${event.error_details}</pre>
        </div>
      ` : ''}
    </div>
  `;
}

/**
 * Initialize theme from saved preference
 */
function initializeTheme() {
  // Get saved theme preference or default to system preference
  const savedTheme = localStorage.getItem('laneswap-theme');
  
  if (savedTheme) {
    applyTheme(savedTheme);
  } else {
    // Check system preference
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(prefersDark ? 'dark' : 'light');
  }
  
  // Update theme toggle button
  updateThemeToggleButton();
}

/**
 * Update theme toggle button appearance
 */
function updateThemeToggleButton() {
  const themeToggleBtn = document.querySelector('.theme-toggle');
  if (!themeToggleBtn) return;
  
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
  const icon = themeToggleBtn.querySelector('.material-symbols-rounded');
  
  if (icon) {
    icon.textContent = currentTheme === 'dark' ? 'light_mode' : 'dark_mode';
  }
}

/**
 * Render service card for grid view
 * @param {Object} service - Service data
 * @returns {string} HTML for the service card
 */
function renderServiceCard(service) {
  const status = service.status?.toLowerCase() || 'unknown';
  const statusCode = service.status_code || '';
  const lastUpdated = formatTimestamp(service.last_updated);
  
  return `
    <div class="service-card" data-service-id="${service.id}" data-status="${status}">
      <div class="service-card-header">
        <h3 class="service-name">${service.name}</h3>
        ${renderStatusSummary(service)}
      </div>
      <div class="service-card-body">
        <div class="service-meta">
          <div class="meta-item">
            <span class="meta-label">Host:</span>
            <span class="meta-value">${service.host || 'N/A'}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Port:</span>
            <span class="meta-value">${service.port || 'N/A'}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Updated:</span>
            <span class="meta-value">${lastUpdated}</span>
          </div>
        </div>
      </div>
      <div class="service-card-footer">
        <button class="btn btn-sm btn-primary view-details-btn" onclick="showServiceDetails('${service.id}')">
          <span class="material-symbols-rounded">visibility</span>
          <span>View Details</span>
        </button>
      </div>
    </div>
  `;
}

/**
 * Render service row for table view
 * @param {Object} service - Service data
 * @returns {string} HTML for the service row
 */
function renderServiceRow(service) {
  const status = service.status?.toLowerCase() || 'unknown';
  const lastUpdated = formatTimestamp(service.last_updated);
  
  return `
    <tr class="service-row" data-service-id="${service.id}" data-status="${status}">
      <td class="service-name-cell">
        <div class="service-name-container">
          <span class="service-name">${service.name}</span>
        </div>
      </td>
      <td class="service-status-cell">
        ${renderStatusSummary(service)}
      </td>
      <td class="service-host-cell">${service.host || 'N/A'}</td>
      <td class="service-port-cell">${service.port || 'N/A'}</td>
      <td class="service-updated-cell">${lastUpdated}</td>
      <td class="service-actions-cell">
        <button class="btn btn-sm btn-primary view-details-btn" onclick="showServiceDetails('${service.id}')">
          <span class="material-symbols-rounded">visibility</span>
        </button>
      </td>
    </tr>
  `;
}

/**
 * Render service status summary with colored indicator
 * @param {Object} service - Service data
 * @returns {string} HTML for the service status summary
 */
function renderStatusSummary(service) {
  const status = service.status?.toLowerCase() || 'unknown';
  const statusCode = service.status_code || '';
  let statusIcon = '';
  
  switch (status) {
    case 'healthy':
      statusIcon = 'check_circle';
      break;
    case 'warning':
      statusIcon = 'warning';
      break;
    case 'error':
      statusIcon = 'error';
      break;
    case 'stale':
      statusIcon = 'schedule';
      break;
    default:
      statusIcon = 'help';
  }
  
  return `
    <div class="status-summary ${status}">
      <div class="status-indicator ${status}"></div>
      <div class="status-text">
        <span>${status.charAt(0).toUpperCase() + status.slice(1)}</span>
        ${statusCode ? `<span class="status-code">${statusCode}</span>` : ''}
      </div>
      <span class="material-symbols-rounded">${statusIcon}</span>
    </div>
  `;
}

/**
 * Render service status with status code
 * @param {Object} service - Service data
 * @returns {string} HTML for the service status
 */
function renderServiceStatus(service) {
  const status = service.status?.toLowerCase() || 'unknown';
  const statusCode = service.status_code || '';
  let statusIcon = '';
  
  switch (status) {
    case 'healthy':
      statusIcon = 'check_circle';
      break;
    case 'warning':
      statusIcon = 'warning';
      break;
    case 'error':
      statusIcon = 'error';
      break;
    case 'stale':
      statusIcon = 'schedule';
      break;
    default:
      statusIcon = 'help';
  }
  
  return `
    <div class="service-status ${status}">
      <span class="material-symbols-rounded">${statusIcon}</span>
      <span>${status.charAt(0).toUpperCase() + status.slice(1)}</span>
      ${statusCode ? `<span class="status-code">${statusCode}</span>` : ''}
    </div>
  `;
}

/**
 * Render status filter items
 * @returns {string} HTML for status filter items
 */
function renderStatusFilters() {
  return `
    <div class="status-filters">
      <div class="status-filter-item all active" data-status="all">
        <span class="status-filter-label">All</span>
      </div>
      <div class="status-filter-item" data-status="healthy">
        <div class="status-indicator healthy"></div>
        <span class="status-filter-label">Healthy</span>
      </div>
      <div class="status-filter-item" data-status="warning">
        <div class="status-indicator warning"></div>
        <span class="status-filter-label">Warning</span>
      </div>
      <div class="status-filter-item" data-status="error">
        <div class="status-indicator error"></div>
        <span class="status-filter-label">Error</span>
      </div>
      <div class="status-filter-item" data-status="stale">
        <div class="status-indicator stale"></div>
        <span class="status-filter-label">Stale</span>
      </div>
    </div>
  `;
}

/**
 * Ensure required DOM elements exist
 * Creates missing elements if needed
 */
function ensureRequiredElements() {
  // Check for main content container
  let mainContent = document.querySelector('.main-content');
  if (!mainContent) {
    console.warn('Main content container not found, creating one');
    const appContainer = document.querySelector('.app-container');
    if (appContainer) {
      mainContent = document.createElement('div');
      mainContent.className = 'main-content';
      appContainer.appendChild(mainContent);
    } else {
      // If app container doesn't exist, create the basic structure
      console.warn('App container not found, creating basic app structure');
      const body = document.body;
      
      const appContainer = document.createElement('div');
      appContainer.className = 'app-container';
      
      mainContent = document.createElement('div');
      mainContent.className = 'main-content';
      
      appContainer.appendChild(mainContent);
      body.appendChild(appContainer);
    }
  }
  
  // Check for services container
  if (!document.getElementById('servicesList')) {
    console.warn('Services container not found, creating one');
    const servicesContainer = document.createElement('div');
    servicesContainer.id = 'servicesList';
    servicesContainer.className = 'services-container grid-view';
    mainContent.appendChild(servicesContainer);
  }
  
  // Check for toast container
  if (!document.getElementById('toastContainer')) {
    console.warn('Toast container not found, creating one');
    const body = document.body;
    const toastContainer = document.createElement('div');
    toastContainer.id = 'toastContainer';
    toastContainer.className = 'toast-container';
    body.appendChild(toastContainer);
  }
  
  // Ensure notification toggle button exists
  if (!document.getElementById('notificationToggleBtn')) {
    console.warn('Notification toggle button not found');
    const headerControls = document.querySelector('.header-controls');
    if (headerControls) {
      const notificationControls = document.createElement('div');
      notificationControls.className = 'btn-group notification-controls';
      
      const notificationBtn = document.createElement('button');
      notificationBtn.id = 'notificationToggleBtn';
      notificationBtn.className = 'btn notification-btn';
      notificationBtn.setAttribute('aria-label', 'Toggle notifications');
      
      const icon = document.createElement('span');
      icon.className = 'material-symbols-rounded';
      icon.textContent = 'notifications_off';
      
      notificationBtn.appendChild(icon);
      notificationControls.appendChild(notificationBtn);
      headerControls.appendChild(notificationControls);
    }
  }
  
  // Ensure summary count elements exist
  const countElements = ['healthyCount', 'warningCount', 'errorCount', 'staleCount', 'totalCount'];
  const summaryContainer = document.querySelector('.monitoring-summary');
  
  if (summaryContainer) {
    // Check if summary elements exist, create them if they don't
    countElements.forEach(id => {
      if (!document.getElementById(id)) {
        console.warn(`Summary count element ${id} not found, creating one`);
        const countElement = document.createElement('span');
        countElement.id = id;
        countElement.className = 'count-value';
        countElement.textContent = '0';
        
        // Create a container for the count element if needed
        const countContainer = document.createElement('div');
        countContainer.className = `count-container ${id.replace('Count', '').toLowerCase()}`;
        countContainer.appendChild(countElement);
        
        summaryContainer.appendChild(countContainer);
      }
    });
  }
  
  // Update elements object with any newly created elements
  elements.servicesList = document.getElementById('servicesList');
  elements.toastContainer = document.getElementById('toastContainer');
  elements.notificationToggleBtn = document.getElementById('notificationToggleBtn');
}

/**
 * Render services based on current view mode
 */
function renderServices() {
  if (!elements.servicesList) {
    console.error('Services container element not found');
    return;
  }
  
  // Clear existing content
  elements.servicesList.innerHTML = '';
  
  // Get filtered services based on search
  const filteredServices = filterServices();
  
  // Check if we have services to display
  if (Object.keys(filteredServices).length === 0) {
    elements.servicesList.innerHTML = `
      <div class="no-services">
        <div class="no-services-icon">
          <span class="material-symbols-rounded">search_off</span>
        </div>
        <div class="no-services-message">
          ${getTranslation('services.noServices') || 'No services found'}
        </div>
      </div>
    `;
    return;
  }
  
  // Render based on view mode
  if (state.viewMode === 'grid') {
    renderServicesGrid(filteredServices);
  } else {
    renderServicesTable(filteredServices);
  }
  
  // Update last updated timestamp
  updateLastUpdated();
}

/**
 * Render services in grid view
 * @param {Object} services - Services to render
 */
function renderServicesGrid(services = null) {
  const servicesToRender = services || filterServices();
  
  // Create grid container
  const gridContainer = document.createElement('div');
  gridContainer.className = 'services-grid';
  
  // Add services to grid
  Object.values(servicesToRender).forEach(service => {
    const serviceCard = document.createElement('div');
    serviceCard.innerHTML = renderServiceCard(service);
    gridContainer.appendChild(serviceCard.firstElementChild);
  });
  
  // Add grid to services container
  elements.servicesList.innerHTML = '';
  elements.servicesList.appendChild(gridContainer);
}

/**
 * Render services in table view
 * @param {Object} services - Services to render
 */
function renderServicesTable(services = null) {
  const servicesToRender = services || filterServices();
  
  // Create table
  const table = document.createElement('table');
  table.className = 'services-table';
  
  // Create table header
  const thead = document.createElement('thead');
  thead.innerHTML = `
    <tr>
      <th class="service-name-header">Name</th>
      <th class="service-status-header">Status</th>
      <th class="service-host-header">Host</th>
      <th class="service-port-header">Port</th>
      <th class="service-updated-header">Last Updated</th>
      <th class="service-actions-header">Actions</th>
    </tr>
  `;
  table.appendChild(thead);
  
  // Create table body
  const tbody = document.createElement('tbody');
  Object.values(servicesToRender).forEach(service => {
    const row = document.createElement('tr');
    row.innerHTML = renderServiceRow(service);
    tbody.appendChild(row.firstElementChild);
  });
  table.appendChild(tbody);
  
  // Add table to services container
  elements.servicesList.innerHTML = '';
  elements.servicesList.appendChild(table);
}

/**
 * Filter services based on search input
 * @returns {Object} Filtered services
 */
function filterServices() {
  const searchTerm = elements.searchInput.value.toLowerCase().trim();
  
  // If no search term, return all services
  if (!searchTerm) {
    return state.services;
  }
  
  // Filter services based on search term
  return Object.values(state.services).reduce((filtered, service) => {
    const serviceName = service.name.toLowerCase();
    const serviceHost = (service.host || '').toLowerCase();
    const serviceStatus = (service.status || '').toLowerCase();
    
    if (
      serviceName.includes(searchTerm) ||
      serviceHost.includes(searchTerm) ||
      serviceStatus.includes(searchTerm)
    ) {
      filtered[service.id] = service;
    }
    
    return filtered;
  }, {});
}

/**
 * Format a timestamp based on user preference
 * @param {string|number} timestamp - The timestamp to format
 * @returns {string} Formatted timestamp
 */
function formatTimestamp(timestamp) {
  if (!timestamp) return 'N/A';
  
  const dateFormat = getStoredValue('laneswap-date-format', 'relative');
  const date = new Date(timestamp);
  
  // Check if date is valid
  if (isNaN(date.getTime())) return 'Invalid date';
  
  switch (dateFormat) {
    case 'relative':
      return getRelativeTime(date);
    case 'absolute':
      return getAbsoluteTime(date);
    case 'iso':
      return date.toISOString();
    default:
      return getRelativeTime(date);
  }
}

/**
 * Get relative time (e.g., "2 minutes ago")
 * @param {Date} date - The date to format
 * @returns {string} Relative time string
 */
function getRelativeTime(date) {
  const now = new Date();
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);
  
  if (diffSec < 60) {
    return `${diffSec} ${diffSec === 1 ? 'second' : 'seconds'} ago`;
  } else if (diffMin < 60) {
    return `${diffMin} ${diffMin === 1 ? 'minute' : 'minutes'} ago`;
  } else if (diffHour < 24) {
    return `${diffHour} ${diffHour === 1 ? 'hour' : 'hours'} ago`;
  } else if (diffDay < 30) {
    return `${diffDay} ${diffDay === 1 ? 'day' : 'days'} ago`;
  } else {
    // Fall back to absolute time for older dates
    return getAbsoluteTime(date);
  }
}

/**
 * Get absolute time (e.g., "Jan 1, 2023 12:34 PM")
 * @param {Date} date - The date to format
 * @returns {string} Absolute time string
 */
function getAbsoluteTime(date) {
  const options = { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  };
  
  return date.toLocaleDateString(undefined, options);
}

/**
 * Get translation for a key
 * @param {string} key - The translation key
 * @returns {string|null} The translated string or null if not found
 */
function getTranslation(key) {
  // Check if translations are available
  if (typeof translations === 'undefined' || !translations[state.currentLanguage]) {
    return null;
  }
  
  // Split the key by dots to access nested properties
  const keys = key.split('.');
  let result = translations[state.currentLanguage];
  
  // Navigate through the nested properties
  for (const k of keys) {
    if (result && typeof result === 'object' && k in result) {
      result = result[k];
    } else {
      return null;
    }
  }
  
  return typeof result === 'string' ? result : null;
}

/**
 * Add enhanced monitoring features
 * Replaces status-summary with more useful metrics
 */
function addEnhancedMonitoring() {
  // Create metrics dashboard
  const metricsDashboard = document.createElement('div');
  metricsDashboard.className = 'metrics-dashboard';
  metricsDashboard.innerHTML = `
    <div class="metrics-header">
      <h3>System Metrics</h3>
      <div class="metrics-actions">
        <button class="btn btn-sm btn-primary refresh-metrics-btn">
          <span class="material-symbols-rounded">refresh</span>
          <span>Refresh</span>
        </button>
      </div>
    </div>
    <div class="metrics-grid">
      ${renderSystemMetrics()}
    </div>
  `;
  
  // Add to main content - safely
  const mainContent = document.querySelector('.main-content');
  if (mainContent) {
    // Insert after the connection section if it exists
    const connectionSection = document.querySelector('.connection-section');
    if (connectionSection) {
      // Use appendChild if nextSibling doesn't exist or insertBefore otherwise
      if (!connectionSection.nextSibling) {
        mainContent.appendChild(metricsDashboard);
      } else {
        try {
          mainContent.insertBefore(metricsDashboard, connectionSection.nextSibling);
        } catch (error) {
          console.warn('Could not insert metrics dashboard at specific position, appending instead', error);
          mainContent.appendChild(metricsDashboard);
        }
      }
    } else {
      // If connection section doesn't exist, just append to main content
      mainContent.appendChild(metricsDashboard);
    }
  }
  
  // Add compact monitoring summary to header
  const monitoringSummary = document.getElementById('monitoringSummary');
  if (monitoringSummary) {
    monitoringSummary.innerHTML = `
      <div class="compact-metrics">
        <div class="compact-metric cpu">
          <span class="material-symbols-rounded">memory</span>
          <span class="compact-value" id="headerCpuUsage">--</span>
        </div>
        <div class="compact-metric memory">
          <span class="material-symbols-rounded">memory_alt</span>
          <span class="compact-value" id="headerMemoryUsage">--</span>
        </div>
        <div class="compact-metric disk">
          <span class="material-symbols-rounded">hard_drive</span>
          <span class="compact-value" id="headerDiskUsage">--</span>
        </div>
      </div>
    `;
  }
  
  // Add event listener for refresh button
  const refreshBtn = metricsDashboard.querySelector('.refresh-metrics-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      updateSystemMetrics();
      showToast('Metrics refreshed', 'success');
    });
  }
  
  // Initial update of metrics
  updateSystemMetrics();
  
  // Set up interval to update metrics
  setInterval(updateSystemMetrics, 10000); // Update every 10 seconds
}

/**
 * Render system metrics cards
 * @returns {string} HTML for system metrics
 */
function renderSystemMetrics() {
  return `
    <div class="metric-card cpu">
      <div class="metric-icon">
        <span class="material-symbols-rounded">memory</span>
      </div>
      <div class="metric-content">
        <h4 class="metric-title">CPU Usage</h4>
        <div class="metric-value" id="cpuUsage">--</div>
        <div class="metric-chart" id="cpuChart"></div>
      </div>
    </div>
    
    <div class="metric-card memory">
      <div class="metric-icon">
        <span class="material-symbols-rounded">memory_alt</span>
      </div>
      <div class="metric-content">
        <h4 class="metric-title">Memory Usage</h4>
        <div class="metric-value" id="memoryUsage">--</div>
        <div class="metric-chart" id="memoryChart"></div>
      </div>
    </div>
    
    <div class="metric-card disk">
      <div class="metric-icon">
        <span class="material-symbols-rounded">hard_drive</span>
      </div>
      <div class="metric-content">
        <h4 class="metric-title">Disk Usage</h4>
        <div class="metric-value" id="diskUsage">--</div>
        <div class="metric-chart" id="diskChart"></div>
      </div>
    </div>
    
    <div class="metric-card network">
      <div class="metric-icon">
        <span class="material-symbols-rounded">lan</span>
      </div>
      <div class="metric-content">
        <h4 class="metric-title">Network Traffic</h4>
        <div class="metric-value" id="networkTraffic">--</div>
        <div class="metric-chart" id="networkChart"></div>
      </div>
    </div>
  `;
}

/**
 * Update system metrics with real data
 */
function updateSystemMetrics() {
  // Simulate fetching system metrics
  const cpuUsage = Math.floor(Math.random() * 100);
  const memoryUsage = Math.floor(Math.random() * 100);
  const diskUsage = Math.floor(Math.random() * 100);
  const networkTraffic = Math.floor(Math.random() * 1000);
  
  // Update main dashboard elements
  const cpuElement = document.getElementById('cpuUsage');
  if (cpuElement) cpuElement.textContent = `${cpuUsage}%`;
  
  const memoryElement = document.getElementById('memoryUsage');
  if (memoryElement) memoryElement.textContent = `${memoryUsage}%`;
  
  const diskElement = document.getElementById('diskUsage');
  if (diskElement) diskElement.textContent = `${diskUsage}%`;
  
  const networkElement = document.getElementById('networkTraffic');
  if (networkElement) networkElement.textContent = `${networkTraffic} KB/s`;
  
  // Update header compact metrics
  const headerCpuElement = document.getElementById('headerCpuUsage');
  if (headerCpuElement) headerCpuElement.textContent = `${cpuUsage}%`;
  
  const headerMemoryElement = document.getElementById('headerMemoryUsage');
  if (headerMemoryElement) headerMemoryElement.textContent = `${memoryUsage}%`;
  
  const headerDiskElement = document.getElementById('headerDiskUsage');
  if (headerDiskElement) headerDiskElement.textContent = `${diskUsage}%`;
  
  // Update charts
  updateMetricChart('cpuChart', cpuUsage, 100);
  updateMetricChart('memoryChart', memoryUsage, 100);
  updateMetricChart('diskChart', diskUsage, 100);
  updateMetricChart('networkChart', networkTraffic, 1000);
}

/**
 * Update a metric chart
 * @param {string} elementId - Chart element ID
 * @param {number} value - Current value
 * @param {number} max - Maximum value
 */
function updateMetricChart(elementId, value, max) {
  const chartElement = document.getElementById(elementId);
  if (!chartElement) return;
  
  // Clear previous chart
  chartElement.innerHTML = '';
  
  // Create progress bar
  const percentage = (value / max) * 100;
  const progressBar = document.createElement('div');
  progressBar.className = 'progress-bar';
  progressBar.innerHTML = `
    <div class="progress-fill" style="width: ${percentage}%"></div>
  `;
  
  // Add color class based on value
  if (percentage > 80) {
    progressBar.classList.add('critical');
  } else if (percentage > 60) {
    progressBar.classList.add('warning');
  } else {
    progressBar.classList.add('normal');
  }
  
  chartElement.appendChild(progressBar);
}

/**
 * Toggle notifications for services
 */
function toggleNotifications() {
  state.notificationsEnabled = !state.notificationsEnabled;
  storeValue('laneswap-notifications-enabled', state.notificationsEnabled);
  updateNotificationToggle();
  
  if (state.notificationsEnabled) {
    showToast('Notifications enabled for services', 'success', 3000, true);
    // Request permission for notifications if needed
    if (Notification && Notification.permission !== 'granted') {
      Notification.requestPermission();
    }
  } else {
    showToast('Notifications disabled for services', 'info', 3000, true);
  }
}

/**
 * Update the notification toggle button state
 */
function updateNotificationToggle() {
  const notificationBtn = document.getElementById('notificationToggleBtn');
  if (notificationBtn) {
    if (state.notificationsEnabled) {
      notificationBtn.classList.add('active');
      notificationBtn.querySelector('.material-symbols-rounded').textContent = 'notifications_active';
    } else {
      notificationBtn.classList.remove('active');
      notificationBtn.querySelector('.material-symbols-rounded').textContent = 'notifications_off';
    }
  }
}

/**
 * Show a browser notification for a service status change
 * @param {Object} service - The service that changed status
 * @param {string} previousStatus - The previous status of the service
 */
function showServiceNotification(service, previousStatus) {
  if (!state.notificationsEnabled || !service) return;
  
  // Only show notifications for status changes
  if (service.status.toLowerCase() === previousStatus) return;
  
  // Check if browser notifications are supported and permission is granted
  if (!("Notification" in window)) {
    console.warn("This browser does not support desktop notifications");
    return;
  }
  
  if (Notification.permission === "granted") {
    const statusText = service.status.charAt(0).toUpperCase() + service.status.slice(1).toLowerCase();
    const notification = new Notification(`Service ${service.name} - ${statusText}`, {
      body: service.message || `Status changed from ${previousStatus} to ${service.status.toLowerCase()}`,
      icon: '/favicon.ico'
    });
    
    // Close the notification after 5 seconds
    setTimeout(() => {
      notification.close();
    }, 5000);
  } else if (Notification.permission !== "denied") {
    Notification.requestPermission().then(permission => {
      if (permission === "granted") {
        showServiceNotification(service, previousStatus);
      }
    });
  }
}

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  try {
    init();
  } catch (error) {
    console.error('Error initializing app:', error);
    // Try to show an error message even if initialization fails
    const servicesList = document.getElementById('servicesList');
    if (servicesList) {
      servicesList.innerHTML = `
        <div class="error-state">
          <span class="material-symbols-rounded error-icon">error</span>
          <p>Error initializing application: ${error.message}</p>
        </div>
      `;
    }
  }
});

/**
 * Initialize the notification toggle
 */
function initializeNotifications() {
  // Check if browser supports notifications
  if (!("Notification" in window)) {
    console.warn("This browser does not support desktop notifications");
    // Hide the notification toggle button
    const notificationBtn = document.getElementById('notificationToggleBtn');
    if (notificationBtn) {
      notificationBtn.style.display = 'none';
    }
    return;
  }
  
  // Load saved notification preference
  state.notificationsEnabled = getStoredValue('laneswap-notifications-enabled', 'false') === 'true';
  
  // Update the toggle button state
  updateNotificationToggle();
  
  // If notifications are enabled, request permission if needed
  if (state.notificationsEnabled && Notification.permission !== 'granted' && Notification.permission !== 'denied') {
    Notification.requestPermission();
  }
}

/**
 * Handle touch events for sidebar swipe gestures
 */
let touchStartX = 0;
let touchEndX = 0;
let isSwiping = false;

function handleTouchStart(e) {
  touchStartX = e.touches[0].clientX;
  isSwiping = true;
}

function handleTouchMove(e) {
  if (!isSwiping) return;
  
  touchEndX = e.touches[0].clientX;
  const touchDiff = touchEndX - touchStartX;
  const screenWidth = window.innerWidth;
  
  // Only handle swipes within 20px of the screen edge or when sidebar is open
  if (touchStartX > 20 && !document.querySelector('.app-container').classList.contains('sidebar-expanded')) {
    return;
  }
  
  // Prevent default scrolling when swiping from edge
  if (touchStartX <= 20 || document.querySelector('.app-container').classList.contains('sidebar-expanded')) {
    e.preventDefault();
  }
}

function handleTouchEnd() {
  if (!isSwiping) return;
  
  const touchDiff = touchEndX - touchStartX;
  const screenWidth = window.innerWidth;
  const appContainer = document.querySelector('.app-container');
  
  // Minimum swipe distance threshold (30px)
  if (Math.abs(touchDiff) > 30) {
    if (touchDiff > 0 && !appContainer.classList.contains('sidebar-expanded')) {
      // Swipe right, open sidebar
      toggleSidebar();
    } else if (touchDiff < 0 && appContainer.classList.contains('sidebar-expanded')) {
      // Swipe left, close sidebar
      toggleSidebar();
    }
  }
  
  isSwiping = false;
  touchStartX = 0;
  touchEndX = 0;
}

// Add event listeners for touch events
document.addEventListener('touchstart', handleTouchStart, { passive: false });
document.addEventListener('touchmove', handleTouchMove, { passive: false });
document.addEventListener('touchend', handleTouchEnd, { passive: true });

// Add click event listener for sidebar overlay
document.querySelector('.sidebar-overlay').addEventListener('click', toggleSidebar);