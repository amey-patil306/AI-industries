// Dashboard JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard
    initializeDashboard();
    
    // Update timestamp every minute
    setInterval(updateTimestamp, 60000);
    
    // Refresh stats every 30 seconds
    setInterval(refreshStats, 30000);
});

function initializeDashboard() {
    console.log('Dashboard initialized');
    updateTimestamp();
    
    // Add smooth scrolling to quick action buttons
    document.querySelectorAll('.quick-action-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            // Add click animation
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

function updateTimestamp() {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    const lastUpdateElement = document.getElementById('last-update');
    if (lastUpdateElement) {
        lastUpdateElement.textContent = timeString;
    }
}

function refreshStats() {
    fetch('/api/dashboard_stats')
        .then(response => response.json())
        .then(data => {
            updateStatCards(data);
        })
        .catch(error => {
            console.error('Error refreshing stats:', error);
        });
}

function updateStatCards(data) {
    // Update camera count
    const cameraCountElement = document.querySelector('.stat-card:nth-child(1) .stat-number');
    if (cameraCountElement) {
        animateNumber(cameraCountElement, data.total_cameras);
    }
    
    // Update alerts count
    const alertsCountElement = document.querySelector('.stat-card:nth-child(2) .stat-number');
    if (alertsCountElement) {
        animateNumber(alertsCountElement, data.alerts_today);
    }
    
    // Update critical alerts
    const criticalAlertsElement = document.querySelector('.stat-card:nth-child(3) .stat-number');
    if (criticalAlertsElement) {
        animateNumber(criticalAlertsElement, data.critical_alerts);
    }
}

function animateNumber(element, newValue) {
    const currentValue = parseInt(element.textContent) || 0;
    const increment = newValue > currentValue ? 1 : -1;
    const duration = 500; // ms
    const steps = Math.abs(newValue - currentValue);
    const stepDuration = duration / steps;
    
    if (steps === 0) return;
    
    let current = currentValue;
    const timer = setInterval(() => {
        current += increment;
        element.textContent = current;
        
        if (current === newValue) {
            clearInterval(timer);
        }
    }, stepDuration);
}

function refreshFeeds() {
    // Add loading state to refresh button
    const refreshBtn = document.querySelector('[onclick="refreshFeeds()"]');
    if (refreshBtn) {
        const originalText = refreshBtn.innerHTML;
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
        refreshBtn.disabled = true;
        
        // Simulate refresh (in real app, this would reload the video feeds)
        setTimeout(() => {
            refreshBtn.innerHTML = originalText;
            refreshBtn.disabled = false;
            
            // Show success message
            showNotification('Camera feeds refreshed successfully', 'success');
        }, 2000);
    }
}

function exportReport() {
    // Show loading state
    showNotification('Generating safety report...', 'info');
    
    // Simulate report generation
    setTimeout(() => {
        // In a real application, this would trigger a download
        const reportData = {
            timestamp: new Date().toISOString(),
            cameras: document.querySelectorAll('.camera-feed-container').length,
            alerts: document.querySelector('.stat-card:nth-child(2) .stat-number')?.textContent || '0',
            uptime: '98.5%'
        };
        
        // Create and download a simple JSON report
        const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `safety-report-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showNotification('Safety report downloaded successfully', 'success');
    }, 1500);
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Camera feed error handling
function handleCameraError(cameraId) {
    const cameraContainer = document.querySelector(`[data-camera-id="${cameraId}"]`);
    if (cameraContainer) {
        const errorMessage = document.createElement('div');
        errorMessage.className = 'camera-error';
        errorMessage.innerHTML = `
            <div class="text-center p-4">
                <i class="fas fa-exclamation-triangle text-warning mb-2" style="font-size: 2rem;"></i>
                <h6>Camera Offline</h6>
                <p class="text-muted mb-0">Unable to connect to camera ${cameraId}</p>
            </div>
        `;
        cameraContainer.appendChild(errorMessage);
    }
}

// Real-time updates (WebSocket simulation)
function simulateRealTimeUpdates() {
    setInterval(() => {
        // Simulate random alert
        if (Math.random() < 0.1) { // 10% chance every interval
            const alertTypes = ['Fire detected', 'PPE violation', 'Intrusion alert', 'Air quality warning'];
            const randomAlert = alertTypes[Math.floor(Math.random() * alertTypes.length)];
            showNotification(randomAlert, 'warning');
        }
    }, 10000); // Check every 10 seconds
}

// Initialize real-time updates
simulateRealTimeUpdates();

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + R for refresh
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        refreshFeeds();
    }
    
    // Ctrl/Cmd + E for export
    if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
        e.preventDefault();
        exportReport();
    }
});