/* Smart RTO Traffic Violation & Command Center Dashboard JS
   - Real-time Virtual Hardware Controller & Polling
   - Web Audio Piezo Buzzer Synthesizer
   - Interactive E-Challan Modal & Print Engine
   - Vahan 4.0 Vehicle Lookup & Scenario Triggers
*/

// --- Web Audio Piezo Buzzer Synthesizer ---
let audioCtx = null;
let soundEnabled = true;

function initAudio() {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) audioCtx = new AudioContext();
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
}

function playBuzzer() {
  if (!soundEnabled) return;
  try {
    initAudio();
    if (!audioCtx) return;

    // Realistic 2.4kHz triple-beep alarm
    const now = audioCtx.currentTime;
    for (let i = 0; i < 3; i++) {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(2400, now + i * 0.18);
      osc.frequency.exponentialRampToValueAtTime(1800, now + i * 0.18 + 0.12);

      gain.gain.setValueAtTime(0.3, now + i * 0.18);
      gain.gain.exponentialRampToValueAtTime(0.01, now + i * 0.18 + 0.12);

      osc.connect(gain);
      gain.connect(audioCtx.destination);

      osc.start(now + i * 0.18);
      osc.stop(now + i * 0.18 + 0.13);
    }
  } catch (e) {
    console.warn("Audio buzzer blocked by browser autoplay policy:", e);
  }
}

function toggleAudio() {
  soundEnabled = !soundEnabled;
  const btn = document.getElementById('btn-sound-toggle');
  if (btn) {
    btn.innerHTML = soundEnabled ? '🔊 Sound: ON' : '🔇 Sound: OFF';
    btn.className = soundEnabled ? 'btn btn-outline-light btn-sm' : 'btn btn-secondary btn-sm';
  }
  toast(soundEnabled ? 'Buzzer audio enabled' : 'Buzzer audio muted');
}

// --- Plate Badge Formatter ---
function plateBadge(vnum) {
  if (!vnum || vnum.includes('Not Clearly')) {
    return `<span class="badge bg-secondary">Unclear Plate</span>`;
  }
  const clean = vnum.replace(/[^A-Z0-9]/gi, '').toUpperCase();
  const state = clean.slice(0, 2);
  const rest = clean.length > 4 ? clean.slice(2, 4) + ' ' + clean.slice(4) : clean.slice(2);
  return `<span class="plate-badge" title="Click to view history" onclick="location.href='/vehicle?q=${clean}'">
    <span class="plate-ind">IND</span>
    <span class="plate-text">${state} ${rest}</span>
  </span>`;
}

// --- Evidence Thumbnail ---
function evImg(v) {
  const src = v.evidence_image ? '/' + v.evidence_image : '/static/placeholder.svg';
  return `<img class="ev" src="${src}" onclick="openChallan(${v.id})" onerror="this.src='/static/placeholder.svg'" title="Click to view E-Challan">`;
}

// --- Row Formatter for Violations ---
function rowHtml(v) {
  const parts = (v.timestamp || '').split('T');
  const d = parts[0] || '';
  const t = (parts[1] || '').slice(0, 8);
  const isPaid = /paid/i.test(v.status || '');
  const isDemo = /demo/i.test(v.status || '');

  let statusBadge = isPaid
    ? `<span class="pill ok">✓ Paid</span>`
    : isDemo
    ? `<span class="pill warn">Simulated</span>`
    : `<span class="pill bad">Pending</span>`;

  return `<tr>
    <td>${plateBadge(v.vehicle_number)}</td>
    <td><span class="fw-bold text-light">${v.violation_type || ''}</span></td>
    <td class="text-secondary mono small">${d}</td>
    <td class="text-secondary mono small">${t}</td>
    <td>${statusBadge}</td>
    <td>${evImg(v)}</td>
    <td>
      <div class="d-flex gap-1">
        <button class="btn btn-outline-light btn-sm px-2 py-1" onclick="openChallan(${v.id})" title="Inspect Official Notice">
          E-Challan
        </button>
        <button class="btn btn-outline-danger btn-sm px-2 py-1" onclick="deleteViolation(${v.id})" title="Delete Record & Evidence">
          ✕
        </button>
      </div>
    </td>
  </tr>`;
}

async function deleteViolation(vid) {
  if (!confirm(`Delete violation record #${vid} and its evidence image permanently?`)) {
    return;
  }
  try {
    const res = await (await fetch(`/api/violations/${vid}`, { method: 'DELETE' })).json();
    if (res.success) {
      toast(`Violation #${vid} deleted successfully`);
      if (typeof loadViolations === 'function') loadViolations();
      if (typeof loadDashboard === 'function') loadDashboard();
    } else {
      toast('Failed to delete: ' + (res.error || 'Unknown error'));
    }
  } catch (e) {
    toast('Error deleting violation: ' + e.message);
  }
}

async function clearAllViolations() {
  if (!confirm('Are you sure you want to permanently clear all violation records and images?')) {
    return;
  }
  try {
    const res = await (await fetch('/api/violations/clear-all', { method: 'POST' })).json();
    if (res.success) {
      toast('All records cleared successfully');
      if (typeof loadViolations === 'function') loadViolations();
      if (typeof loadDashboard === 'function') loadDashboard();
    }
  } catch (e) {
    toast('Error clearing records: ' + e.message);
  }
}



// --- Toast System ---
function toast(msg, type = 'info') {
  const box = document.getElementById('toasts');
  if (!box) return;
  const el = document.createElement('div');
  el.className = 'toast-msg';
  el.innerHTML = `<div>${msg}</div>`;
  box.appendChild(el);
  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateX(30px)';
    setTimeout(() => el.remove(), 300);
  }, 4500);
}

// --- Telemetry Strip Updater ---
function setPill(id, text, cls) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = text;
  el.className = 'pill ' + (cls || '');
}

let lastSignalState = '';
let buzzerTriggeredOnce = false;

async function refreshStrip() {
  try {
    const s = await (await fetch('/api/system/status')).json();
    const sig = s.signal_state || 'UNKNOWN';
    const countdown = s.countdown != null ? `${s.countdown}s` : '';

    // Update Signal Pill
    setPill('sys-signal',
      `<span class="live-pulse" style="background:${sig==='RED'?'#ff4757':sig==='YELLOW'?'#ffa502':'#2ed573'};box-shadow:0 0 8px ${sig==='RED'?'#ff4757':sig==='YELLOW'?'#ffa502':'#2ed573'}"></span> Signal: <b>${sig}</b> ${countdown ? `(${countdown})` : ''}`,
      sig === 'RED' ? 'signal-RED' : sig === 'YELLOW' ? 'signal-YELLOW' : sig === 'GREEN' ? 'signal-GREEN' : 'warn');

    // Update Hardware Pill
    const ard = s.arduino || '?';
    setPill('sys-arduino', `Controller: <b>${ard}</b>`, /CONNECTED/.test(ard) || /ACTIVE/.test(ard) ? 'ok' : 'warn');

    // Update Camera Pill
    const cam = s.camera || '?';
    setPill('sys-camera', `Camera: <b>${cam}</b>`, /CONNECTED/.test(cam) || /SIMULATED/.test(cam) ? 'ok' : 'bad');

    // Update DB
    setPill('sys-db', `DB: <b>CONNECTED</b>`, 'ok');

    // Sound buzzer if active
    if (s.buzzer && !buzzerTriggeredOnce) {
      playBuzzer();
      buzzerTriggeredOnce = true;
    } else if (!s.buzzer) {
      buzzerTriggeredOnce = false;
    }

    lastSignalState = sig;
    return s;
  } catch (e) {
    setPill('sys-signal', 'Signal: offline', 'bad');
    return null;
  }
}

// --- Virtual Hardware API Controls ---
async function setSignal(state) {
  initAudio();
  try {
    const res = await (await fetch('/api/hardware/signal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state: state })
    })).json();
    toast(`Signal changed to <b>${state}</b>`);
    refreshStrip();
  } catch (e) {
    toast('Failed to change signal: ' + e.message);
  }
}

async function triggerIRBeam(vehicleNumber = 'MH15AB1234', violationType = 'Red Light Violation') {
  initAudio();
  try {
    const res = await (await fetch('/api/hardware/trigger-ir', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ vehicle_number: vehicleNumber, violation_type: violationType })
    })).json();

    if (res.violation) {
      playBuzzer();
      toast(`🚨 <b>${res.message}</b> for ${vehicleNumber}`);
    } else {
      toast(`ℹ️ ${res.message}`);
    }

    // Trip laser visual on live page if present
    const laser = document.getElementById('ir-laser');
    if (laser) {
      laser.classList.add('tripped');
      setTimeout(() => laser.classList.remove('tripped'), 2500);
    }

    if (typeof loadDashboard === 'function') loadDashboard();
    if (typeof refreshLive === 'function') refreshLive();
    refreshStrip();
  } catch (e) {
    toast('Error triggering IR: ' + e.message);
  }
}

// Spacebar shortcut: tap Spacebar anywhere on the page to instantly trigger stop-line violation!
document.addEventListener('keydown', (e) => {
  if (['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return;
  if (e.code === 'Space') {
    e.preventDefault();
    triggerIRBeam();
  }
});


async function runScenario(scenarioId) {
  initAudio();
  try {
    const res = await (await fetch('/api/hardware/scenario', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: scenarioId })
    })).json();

    if (res.scenario.type === 'Red Light Violation') {
      playBuzzer();
    }

    toast(`Executed: <b>${res.scenario.desc}</b> (${res.scenario.vehicle})`);
    if (typeof loadDashboard === 'function') loadDashboard();
    if (typeof refreshLive === 'function') refreshLive();
    refreshStrip();
  } catch (e) {
    toast('Scenario execution error: ' + e.message);
  }
}

// --- Official E-Challan Modal Dialog Engine ---
async function openChallan(vid) {
  initAudio();
  try {
    const data = await (await fetch('/api/challan/' + vid)).json();
    if (data.error) {
      toast('Challan not found');
      return;
    }

    let modalEl = document.getElementById('challanModal');
    if (!modalEl) {
      modalEl = document.createElement('div');
      modalEl.id = 'challanModal';
      modalEl.className = 'modal fade';
      modalEl.tabIndex = -1;
      document.body.appendChild(modalEl);
    }

    const isPaid = (data.payment_status === 'PAID');
    const evImgSrc = data.evidence_image ? '/' + data.evidence_image : '/static/placeholder.svg';

    modalEl.innerHTML = `
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title fw-bold">🏛️ Ministry of Road Transport & Highways — E-Challan Notice</h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body p-4">
            <div class="challan-cert" id="printable-challan">
              <div class="challan-header">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <span class="badge bg-primary text-uppercase">${data.rto_office}</span>
                  <span class="badge ${isPaid ? 'bg-success' : 'bg-danger'} fs-6">${data.payment_status}</span>
                </div>
                <h4>MAHARASHTRA MOTOR VEHICLES DEPARTMENT</h4>
                <h6>TRAFFIC ENFORCEMENT & VIOLATION NOTICE UNDER MOTOR VEHICLES ACT</h6>
                <div class="small text-muted mono mt-1">Challan No: <b>${data.challan_number}</b> | Issued: ${data.timestamp}</div>
              </div>

              <div class="row g-3">
                <div class="col-md-7">
                  <div class="challan-grid">
                    <div class="challan-field"><small>Registration Number</small><b>${data.vehicle_number}</b></div>
                    <div class="challan-field"><small>Registered Owner</small><b>${data.owner_name}</b></div>
                    <div class="challan-field"><small>Vehicle Class / Model</small><b>${data.vehicle_class}<br><span class="text-muted">${data.model}</span></b></div>
                    <div class="challan-field"><small>Registered Mobile</small><b>${data.mobile_masked}</b></div>
                    <div class="challan-field"><small>Offense / Rule Violated</small><b class="text-danger">${data.violation_type}</b></div>
                    <div class="challan-field"><small>MVA Legal Section</small><b class="mono small">${data.mva_section}</b></div>
                    <div class="challan-field"><small>Junction Location</small><b>${data.location}</b></div>
                    <div class="challan-field"><small>Payment Due Date</small><b>${data.due_date}</b></div>
                  </div>

                  <div class="challan-fine-box">
                    <div>
                      <small class="text-muted d-block text-uppercase fw-bold">Total Compounding Penalty</small>
                      <span class="challan-fine-amount">₹${data.fine_amount.toLocaleString('en-IN')}</span>
                      <small class="text-danger d-block mono">(Demerit Points: +${data.demerit_points})</small>
                    </div>
                    <div class="challan-qr text-center">
                      <div class="mono" style="font-size:0.6rem;line-height:1.1;color:#1e3a8a">
                        <b>UPI SCAN</b><br>
                        <svg width="60" height="60" viewBox="0 0 100 100">
                          <rect width="100" height="100" fill="#fff"/>
                          <rect x="10" y="10" width="30" height="30" fill="#000"/>
                          <rect x="16" y="16" width="18" height="18" fill="#fff"/>
                          <rect x="20" y="20" width="10" height="10" fill="#000"/>
                          <rect x="60" y="10" width="30" height="30" fill="#000"/>
                          <rect x="66" y="16" width="18" height="18" fill="#fff"/>
                          <rect x="70" y="20" width="10" height="10" fill="#000"/>
                          <rect x="10" y="60" width="30" height="30" fill="#000"/>
                          <rect x="16" y="66" width="18" height="18" fill="#fff"/>
                          <rect x="20" y="70" width="10" height="10" fill="#000"/>
                          <rect x="50" y="50" width="15" height="15" fill="#000"/>
                          <rect x="70" y="60" width="20" height="10" fill="#000"/>
                          <rect x="70" y="75" width="10" height="15" fill="#000"/>
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="col-md-5">
                  <div class="text-muted small fw-bold mb-1">AUTOMATED CCTV EVIDENCE PHOTO</div>
                  <div class="border rounded overflow-hidden" style="background:#000">
                    <img src="${evImgSrc}" class="w-100" style="max-height:210px;object-fit:contain" alt="Evidence Snapshot">
                  </div>
                  <div class="small text-muted mt-2">
                    <b>Confidence:</b> ${(data.confidence * 100).toFixed(1)}% | <b>Camera:</b> Junction CCTV #02
                  </div>
                  <div class="alert alert-warning p-2 mt-2 small mb-0">
                    ⚠️ Failure to pay compounding fees within 60 days will result in automated court summons under Section 208 MVA.
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-light" onclick="window.print()">🖨️ Print / Download PDF</button>
            ${!isPaid ? `<button type="button" class="btn btn-success" onclick="payChallan(${data.violation_id})">💳 Pay Online (Simulate UPI)</button>` : `<button type="button" class="btn btn-outline-success disabled">✓ Paid in Full</button>`}
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    `;

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
  } catch (e) {
    toast('Error opening challan: ' + e.message);
  }
}

async function payChallan(vid) {
  try {
    const res = await (await fetch(`/api/violations/${vid}/pay`, { method: 'POST' })).json();
    if (res.success) {
      toast(`✅ Challan #${vid} marked as PAID via UPI Gateway!`);
      const modalEl = document.getElementById('challanModal');
      if (modalEl) {
        const bsModal = bootstrap.Modal.getInstance(modalEl);
        if (bsModal) bsModal.hide();
      }
      if (typeof loadDashboard === 'function') loadDashboard();
      if (typeof loadViolations === 'function') loadViolations();
    }
  } catch (e) {
    toast('Payment error: ' + e.message);
  }
}

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
  refreshStrip();
  setInterval(refreshStrip, 2000);

  // Enable audio context on any user click
  document.body.addEventListener('click', () => {
    if (!audioCtx) initAudio();
  }, { once: true });
});
