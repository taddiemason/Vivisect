// Vivisect Web GUI Application

// Initialize Socket.IO
const socket = io();

// State
let currentTab = 'dashboard';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    initializeClock();
    loadSystemStatus();
    setupSocketListeners();
    log('System initialized', 'success');
});

// Tab Management
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.getAttribute('data-tab');
            showTab(tabName);
        });
    });
}

function showTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-tab') === tabName) {
            btn.classList.add('active');
        }
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');

    currentTab = tabName;
}

// Clock
function initializeClock() {
    updateClock();
    setInterval(updateClock, 1000);
}

function updateClock() {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    document.getElementById('clock').textContent = timeString;
}

// System Status
function loadSystemStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                document.getElementById('active-tasks').textContent = data.active_tasks;
                document.getElementById('output-dir').textContent = data.output_dir;

                // Update USB status
                const usbStatus = document.getElementById('usb-status');
                if (data.usb_connected) {
                    usbStatus.innerHTML = '✅ Connected to Host PC';
                    usbStatus.style.color = '#10b981';
                } else {
                    usbStatus.innerHTML = '⭕ Not Connected';
                    usbStatus.style.color = '#64748b';
                }

                updateStatusIndicator('connected');
            }
        })
        .catch(error => {
            console.error('Error loading status:', error);
            updateStatusIndicator('error');
        });

    // Load multi-function USB status
    loadMultiFunctionStatus();
}

function loadMultiFunctionStatus() {
    fetch('/api/usb/multifunction-status')
        .then(response => response.json())
        .then(data => {
            if (!data.error && data.functions) {
                // Update network status
                const networkStatus = document.getElementById('usb-network-status');
                if (networkStatus) {
                    if (data.functions.network.connected) {
                        networkStatus.innerHTML = '✅ Network Active';
                        networkStatus.style.color = '#10b981';
                    } else {
                        networkStatus.innerHTML = '⭕ Network Inactive';
                        networkStatus.style.color = '#64748b';
                    }
                }

                // Update mass storage status
                const storageStatus = document.getElementById('usb-storage-status');
                if (storageStatus) {
                    if (data.functions.mass_storage.available) {
                        const sizeMB = data.functions.mass_storage.size_mb || 0;
                        storageStatus.innerHTML = `💾 Storage (${sizeMB}MB)`;
                        storageStatus.style.color = '#10b981';
                    } else {
                        storageStatus.innerHTML = '💾 Storage Not Available';
                        storageStatus.style.color = '#64748b';
                    }
                }

                // Update serial status
                const serialStatus = document.getElementById('usb-serial-status');
                if (serialStatus) {
                    if (data.functions.serial.available) {
                        serialStatus.innerHTML = '⌨️ Serial Console';
                        serialStatus.style.color = '#10b981';
                    } else {
                        serialStatus.innerHTML = '⌨️ Serial Inactive';
                        serialStatus.style.color = '#64748b';
                    }
                }

                // Update mode indicator
                const modeIndicator = document.getElementById('usb-mode');
                if (modeIndicator) {
                    modeIndicator.textContent = data.active_mode || data.mode || 'Unknown';
                }
            }
        })
        .catch(error => {
            console.error('Error loading multi-function status:', error);
        });
}

function updateStatusIndicator(status) {
    const indicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');

    switch(status) {
        case 'connected':
            indicator.style.background = '#10b981';
            statusText.textContent = 'Connected';
            break;
        case 'processing':
            indicator.style.background = '#f59e0b';
            statusText.textContent = 'Processing';
            break;
        case 'error':
            indicator.style.background = '#ef4444';
            statusText.textContent = 'Error';
            break;
        default:
            indicator.style.background = '#64748b';
            statusText.textContent = 'Unknown';
    }
}

// Socket.IO Event Listeners
function setupSocketListeners() {
    socket.on('connected', (data) => {
        log('Connected to server', 'success');
        updateStatusIndicator('connected');
    });

    socket.on('task_complete', (data) => {
        hideProgress();
        log(`Task ${data.task} completed`, 'success');

        if (data.result && data.result.success === false) {
            alert(`Error: ${data.result.error}`);
        } else {
            alert(`Task ${data.task} completed successfully!`);
        }

        loadSystemStatus();
    });

    socket.on('progress', (data) => {
        updateProgress(data);
    });

    socket.on('disconnect', () => {
        log('Disconnected from server', 'error');
        updateStatusIndicator('error');
    });
}

// Activity Log
function log(message, type = 'info') {
    const logDisplay = document.getElementById('activity-log');
    const timestamp = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `[${timestamp}] ${message}`;
    logDisplay.insertBefore(entry, logDisplay.firstChild);

    // Keep only last 50 entries
    while (logDisplay.children.length > 50) {
        logDisplay.removeChild(logDisplay.lastChild);
    }
}

// Progress Overlay
function showProgress(text = 'Processing...') {
    document.getElementById('progress-overlay').classList.remove('hidden');
    document.getElementById('progress-text').textContent = text;
    document.getElementById('progress-fill').style.width = '10%';
    updateStatusIndicator('processing');
}

function hideProgress() {
    document.getElementById('progress-overlay').classList.add('hidden');
    updateStatusIndicator('connected');
}

function updateProgress(data) {
    const text = `${data.step}: ${data.status}`;
    document.getElementById('progress-text').textContent = text;
    log(text, 'info');

    // Animate progress bar
    const fill = document.getElementById('progress-fill');
    const currentWidth = parseInt(fill.style.width) || 10;
    fill.style.width = Math.min(currentWidth + 20, 90) + '%';
}

// Disk Imaging Functions
function listDevices() {
    showProgress('Loading devices...');
    fetch('/api/disk/devices')
        .then(response => response.json())
        .then(data => {
            hideProgress();
            if (data.error) {
                alert('Error: ' + data.error);
                return;
            }

            const container = document.getElementById('devices-list');
            container.innerHTML = '';

            if (data.devices.length === 0) {
                container.innerHTML = '<p style="color: var(--text-muted);">No devices found</p>';
                return;
            }

            data.devices.forEach(device => {
                const card = document.createElement('div');
                card.className = 'device-card';
                card.innerHTML = `
                    <div class="device-name">💿 ${device.name}</div>
                    <div class="device-info">Size: ${device.size}</div>
                    <div class="device-info">Type: ${device.type}</div>
                `;
                card.onclick = () => {
                    document.querySelectorAll('.device-card').forEach(c => c.classList.remove('selected'));
                    card.classList.add('selected');
                    document.getElementById('disk-device').value = '/dev/' + device.name;
                };
                container.appendChild(card);
            });

            log(`Found ${data.devices.length} devices`, 'success');
        })
        .catch(error => {
            hideProgress();
            alert('Error loading devices: ' + error);
            log('Error loading devices', 'error');
        });
}

function createDiskImage() {
    const device = document.getElementById('disk-device').value;
    const output = document.getElementById('disk-output').value;
    const method = document.getElementById('disk-method').value;

    if (!device || !output) {
        alert('Please enter device and output filename');
        return;
    }

    if (!confirm(`Create disk image of ${device}?\n\nThis may take a long time depending on disk size.`)) {
        return;
    }

    showProgress(`Creating disk image of ${device}...`);

    fetch('/api/disk/image', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({device, output, method})
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            hideProgress();
            alert('Error: ' + data.error);
        } else {
            log(`Disk imaging started: ${device} -> ${output}`, 'success');
        }
    })
    .catch(error => {
        hideProgress();
        alert('Error: ' + error);
        log('Disk imaging error', 'error');
    });
}

// Network Functions
function listInterfaces() {
    showProgress('Loading network interfaces...');
    fetch('/api/network/interfaces')
        .then(response => response.json())
        .then(data => {
            hideProgress();
            if (data.error) {
                alert('Error: ' + data.error);
                return;
            }

            const container = document.getElementById('interfaces-list');
            container.innerHTML = '';

            if (data.interfaces.length === 0) {
                container.innerHTML = '<p style="color: var(--text-muted);">No interfaces found</p>';
                return;
            }

            data.interfaces.forEach(iface => {
                const card = document.createElement('div');
                card.className = 'device-card';
                card.innerHTML = `
                    <div class="device-name">📡 ${iface.name || 'Unknown'}</div>
                    <div class="device-info">State: ${iface.state || 'Unknown'}</div>
                    <div class="device-info">MAC: ${iface.mac || 'N/A'}</div>
                `;
                card.onclick = () => {
                    document.querySelectorAll('#interfaces-list .device-card').forEach(c => c.classList.remove('selected'));
                    card.classList.add('selected');
                    document.getElementById('net-interface').value = iface.name;
                };
                container.appendChild(card);
            });

            log(`Found ${data.interfaces.length} network interfaces`, 'success');
        })
        .catch(error => {
            hideProgress();
            alert('Error loading interfaces: ' + error);
            log('Error loading interfaces', 'error');
        });
}

function startCapture() {
    const iface = document.getElementById('net-interface').value;
    const output = document.getElementById('net-output').value;
    const duration = document.getElementById('net-duration').value;

    if (!iface || !output) {
        alert('Please enter interface and output filename');
        return;
    }

    showProgress(`Capturing traffic on ${iface} for ${duration} seconds...`);

    fetch('/api/network/capture', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({interface: iface, output, duration: parseInt(duration)})
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            hideProgress();
            alert('Error: ' + data.error);
        } else {
            log(`Network capture started on ${iface}`, 'success');
        }
    })
    .catch(error => {
        hideProgress();
        alert('Error: ' + error);
        log('Network capture error', 'error');
    });
}

// Memory Functions
function analyzeLive() {
    showProgress('Analyzing running system...');
    fetch('/api/memory/live')
        .then(response => response.json())
        .then(data => {
            hideProgress();
            if (data.error) {
                alert('Error: ' + data.error);
                return;
            }

            const container = document.getElementById('memory-results');
            container.innerHTML = `
                <h3>Live System Analysis</h3>
                <div class="status-item">
                    <span class="label">Processes:</span>
                    <span>${data.processes ? data.processes.length : 0}</span>
                </div>
                <div class="status-item">
                    <span class="label">Network Connections:</span>
                    <span>${data.network ? data.network.length : 0}</span>
                </div>
                <div class="status-item">
                    <span class="label">Loaded Modules:</span>
                    <span>${data.loaded_modules ? data.loaded_modules.length : 0}</span>
                </div>
                <div class="status-item">
                    <span class="label">Timestamp:</span>
                    <span>${data.timestamp || 'N/A'}</span>
                </div>
            `;

            log('Live memory analysis completed', 'success');
        })
        .catch(error => {
            hideProgress();
            alert('Error: ' + error);
            log('Memory analysis error', 'error');
        });
}

function createMemoryDump() {
    const output = document.getElementById('mem-output').value;
    const method = document.getElementById('mem-method').value;

    if (!output) {
        alert('Please enter output filename');
        return;
    }

    if (!confirm('Create memory dump?\n\nThis may take several minutes.')) {
        return;
    }

    showProgress('Creating memory dump...');

    fetch('/api/memory/dump', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({output, method})
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            hideProgress();
            alert('Error: ' + data.error);
        } else {
            log(`Memory dump started: ${output}`, 'success');
        }
    })
    .catch(error => {
        hideProgress();
        alert('Error: ' + error);
        log('Memory dump error', 'error');
    });
}

// Artifact Functions
function extractBrowser() {
    showProgress('Extracting browser artifacts...');
    fetch('/api/artifacts/browser')
        .then(response => response.json())
        .then(data => {
            hideProgress();
            if (data.error) {
                alert('Error: ' + data.error);
                return;
            }

            const container = document.getElementById('artifacts-results');
            const chromeCount = data.chrome ? data.chrome.length : 0;
            const firefoxCount = data.firefox ? data.firefox.length : 0;

            container.innerHTML = `
                <h3>Browser Artifacts</h3>
                <div class="status-item">
                    <span class="label">Chrome Entries:</span>
                    <span>${chromeCount}</span>
                </div>
                <div class="status-item">
                    <span class="label">Firefox Entries:</span>
                    <span>${firefoxCount}</span>
                </div>
                <div class="status-item">
                    <span class="label">Total:</span>
                    <span>${chromeCount + firefoxCount}</span>
                </div>
            `;

            log(`Extracted browser history: ${chromeCount + firefoxCount} entries`, 'success');
        })
        .catch(error => {
            hideProgress();
            alert('Error: ' + error);
            log('Browser extraction error', 'error');
        });
}

function extractLogs() {
    showProgress('Extracting system logs...');
    fetch('/api/artifacts/logs')
        .then(response => response.json())
        .then(data => {
            hideProgress();
            if (data.error) {
                alert('Error: ' + data.error);
                return;
            }

            const container = document.getElementById('artifacts-results');
            let html = '<h3>System Logs</h3>';

            for (const [logType, entries] of Object.entries(data)) {
                if (Array.isArray(entries)) {
                    html += `
                        <div class="status-item">
                            <span class="label">${logType}:</span>
                            <span>${entries.length} entries</span>
                        </div>
                    `;
                }
            }

            container.innerHTML = html;
            log('System logs extracted', 'success');
        })
        .catch(error => {
            hideProgress();
            alert('Error: ' + error);
            log('Log extraction error', 'error');
        });
}

function extractPersistence() {
    showProgress('Extracting persistence mechanisms...');
    fetch('/api/artifacts/persistence')
        .then(response => response.json())
        .then(data => {
            hideProgress();
            if (data.error) {
                alert('Error: ' + data.error);
                return;
            }

            const container = document.getElementById('artifacts-results');
            let html = '<h3>Persistence Mechanisms</h3>';

            for (const [mechType, items] of Object.entries(data)) {
                if (Array.isArray(items)) {
                    html += `
                        <div class="status-item">
                            <span class="label">${mechType}:</span>
                            <span>${items.length} items</span>
                        </div>
                    `;
                }
            }

            container.innerHTML = html;
            log('Persistence mechanisms extracted', 'success');
        })
        .catch(error => {
            hideProgress();
            alert('Error: ' + error);
            log('Persistence extraction error', 'error');
        });
}

// Collection Function
function runCollection() {
    const caseId = document.getElementById('case-id').value.trim();

    if (!confirm(`Run full forensics collection?\n\nCase ID: ${caseId || 'Auto-generated'}\n\nThis may take several minutes.`)) {
        return;
    }

    showProgress('Running forensics collection...');

    fetch('/api/collect', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({case_id: caseId})
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            hideProgress();
            alert('Error: ' + data.error);
        } else {
            log(`Collection started: ${data.case_id}`, 'success');
        }
    })
    .catch(error => {
        hideProgress();
        alert('Error: ' + error);
        log('Collection error', 'error');
    });
}

// Reports Functions
function listReports() {
    showProgress('Loading reports...');
    fetch('/api/reports')
        .then(response => response.json())
        .then(data => {
            hideProgress();
            if (data.error) {
                alert('Error: ' + data.error);
                return;
            }

            const container = document.getElementById('reports-list');
            container.innerHTML = '';

            if (data.reports.length === 0) {
                container.innerHTML = '<p style="color: var(--text-muted);">No reports found</p>';
                return;
            }

            data.reports.forEach(report => {
                const card = document.createElement('div');
                card.className = 'report-card';

                const fileSize = (report.size / 1024).toFixed(2);
                const modified = new Date(report.modified).toLocaleString();

                card.innerHTML = `
                    <div class="report-info">
                        <div class="report-name">📄 ${report.filename}</div>
                        <div class="report-meta">${fileSize} KB • ${modified}</div>
                    </div>
                    <div class="report-actions">
                        <button class="btn btn-secondary" onclick="downloadReport('${report.filename}')">
                            Download
                        </button>
                    </div>
                `;
                container.appendChild(card);
            });

            log(`Found ${data.reports.length} reports`, 'success');
        })
        .catch(error => {
            hideProgress();
            alert('Error loading reports: ' + error);
            log('Error loading reports', 'error');
        });
}

function downloadReport(filename) {
    window.open(`/api/reports/${filename}`, '_blank');
    log(`Downloading report: ${filename}`, 'success');
}

// USB Mode Switching Functions
function switchUSBMode(mode) {
    const modeNames = {
        'multi': 'Multi-Function (Network + Storage + Serial)',
        'mass_storage': 'USB Flash Drive (Read-Write)',
        'mass_storage_ro': 'USB Flash Drive (Read-Only)',
        'network': 'Network Only (USB Ethernet)'
    };

    if (!confirm(`Switch to ${modeNames[mode]}?\n\nThis will disconnect and reconnect the USB device.`)) {
        return;
    }

    showProgress(`Switching to ${modeNames[mode]}...`);
    log(`Switching USB mode to: ${mode}`, 'info');

    const payload = {
        mode: mode === 'mass_storage_ro' ? 'mass_storage' : mode,
        read_only: mode === 'mass_storage_ro'
    };

    fetch('/api/usb/mode/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        hideProgress();
        if (data.error) {
            alert('Error switching mode: ' + data.error);
            log('USB mode switch failed', 'error');
        } else if (data.success) {
            log(data.message || 'USB mode switched successfully', 'success');
            // Reload status after mode switch
            setTimeout(loadSystemStatus, 2000);
        } else {
            alert('Mode switch failed');
            log('USB mode switch failed', 'error');
        }
    })
    .catch(error => {
        hideProgress();
        alert('Error: ' + error);
        log('USB mode switch error', 'error');
    });
}

// HID Keyboard Functions
function loadHIDStatus() {
    fetch('/api/usb/hid/status')
        .then(response => response.json())
        .then(data => {
            const statusElem = document.getElementById('hid-status');
            if (statusElem) {
                if (data.available) {
                    statusElem.innerHTML = '✅ HID Available';
                    statusElem.style.color = '#10b981';
                } else {
                    statusElem.innerHTML = '⭕ HID Not Available';
                    statusElem.style.color = '#64748b';
                }
            }
        })
        .catch(error => {
            console.error('Error loading HID status:', error);
        });
}

function loadHIDPayloads() {
    fetch('/api/usb/hid/payloads')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error loading payloads: ' + data.error);
                return;
            }

            const select = document.getElementById('hid-payload-select');
            if (select) {
                select.innerHTML = '<option value="">Select a payload...</option>';

                data.payloads.forEach(name => {
                    const option = document.createElement('option');
                    option.value = name;
                    const desc = data.details[name]?.description || name;
                    option.textContent = `${name} - ${desc}`;
                    select.appendChild(option);
                });
            }

            log(`Loaded ${data.payloads.length} HID payloads`, 'success');
        })
        .catch(error => {
            console.error('Error loading payloads:', error);
        });
}

function sendHIDString() {
    const text = document.getElementById('hid-text-input').value;
    const delay = document.getElementById('hid-delay').value || 50;

    if (!text) {
        alert('Please enter text to send');
        return;
    }

    if (!confirm(`⚠️ AUTHORIZATION WARNING ⚠️\n\nYou are about to send keystrokes via HID mode:\n"${text.substring(0, 100)}${text.length > 100 ? '...' : ''}"\n\nConfirm you have authorization to use HID mode on the connected system.`)) {
        return;
    }

    showProgress('Sending HID keystrokes...');
    log(`Sending HID string (${text.length} chars)`, 'info');

    fetch('/api/usb/hid/send-string', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text, delay_ms: parseInt(delay)})
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            hideProgress();
            alert('Error: ' + data.error);
            log('HID send string failed', 'error');
        } else {
            log(`HID string sent (task ${data.task_id})`, 'success');
        }
    })
    .catch(error => {
        hideProgress();
        alert('Error: ' + error);
        log('HID send string error', 'error');
    });
}

function executeHIDPayload() {
    const payloadName = document.getElementById('hid-payload-select').value;

    if (!payloadName) {
        alert('Please select a payload');
        return;
    }

    if (!confirm(`⚠️ AUTHORIZATION WARNING ⚠️\n\nYou are about to execute HID payload:\n"${payloadName}"\n\nThis will send automated keystrokes to the connected system.\n\nConfirm you have explicit authorization for this action.`)) {
        return;
    }

    showProgress(`Executing HID payload: ${payloadName}...`);
    log(`Executing HID payload: ${payloadName}`, 'info');

    fetch('/api/usb/hid/execute-payload', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({payload_name: payloadName})
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            hideProgress();
            alert('Error: ' + data.error);
            log('HID payload execution failed', 'error');
        } else {
            log(`HID payload ${payloadName} started (task ${data.task_id})`, 'success');
        }
    })
    .catch(error => {
        hideProgress();
        alert('Error: ' + error);
        log('HID payload execution error', 'error');
    });
}

function switchToHIDMode() {
    if (!confirm(`⚠️ CRITICAL WARNING ⚠️\n\nYou are about to switch to HID Keyboard Mode.\n\nHID mode enables automated keystroke injection (BadUSB functionality).\n\nBy proceeding, you confirm:\n1. You have explicit written authorization\n2. This is for legitimate security testing or forensics\n3. You understand legal and ethical implications\n\nProceed with HID mode switch?`)) {
        return;
    }

    showProgress('Switching to HID Keyboard Mode...');
    log('Switching to HID mode', 'info');

    fetch('/api/usb/hid/mode/switch', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        hideProgress();
        if (data.error) {
            alert('Error switching to HID mode: ' + data.error);
            log('HID mode switch failed', 'error');
        } else if (data.success) {
            log(data.message || 'HID mode activated', 'success');
            setTimeout(() => {
                loadSystemStatus();
                loadHIDStatus();
            }, 2000);
        } else {
            alert('HID mode switch failed');
            log('HID mode switch failed', 'error');
        }
    })
    .catch(error => {
        hideProgress();
        alert('Error: ' + error);
        log('HID mode switch error', 'error');
    });
}

// Auto-refresh status every 30 seconds
setInterval(loadSystemStatus, 30000);

// Auto-load reports when tab is opened
const reportsTab = document.querySelector('[data-tab="reports"]');
if (reportsTab) {
    reportsTab.addEventListener('click', listReports);
}

// Auto-load HID payloads on page load
document.addEventListener('DOMContentLoaded', function() {
    loadHIDPayloads();
    loadHIDStatus();
});
