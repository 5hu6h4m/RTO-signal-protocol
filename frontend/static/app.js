/* Shared helpers for all pages: rows, status strip, toasts, feed watchdog. */
function evImg(v) {
  const src = v.evidence_image ? '/' + v.evidence_image : '/static/placeholder.svg';
  return `<a href="${src}" target="_blank"><img class="ev" src="${src}" onerror="this.src='/static/placeholder.svg'"></a>`;
}
function rowHtml(v) {
  const parts = (v.timestamp || '').split('T');
  const d = parts[0] || '', t = (parts[1] || '').slice(0, 8);
  const badge = /Demo/i.test(v.status || '') ? 'warn' : 'bad';
  return `<tr><td><b>${v.vehicle_number || ''}</b></td><td>${v.violation_type || ''}</td>` +
    `<td>${d}</td><td>${t}</td><td><span class="pill ${badge}">${v.status || ''}</span></td><td>${evImg(v)}</td></tr>`;
}
function toast(msg) {
  const box = document.getElementById('toasts');
  if (!box) return;
  const el = document.createElement('div');
  el.className = 'toast-msg';
  el.textContent = msg;
  box.appendChild(el);
  setTimeout(() => el.remove(), 6000);
}
function setPill(id, text, cls) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  el.className = 'pill ' + (cls || '');
}
async function refreshStrip() {
  try {
    const s = await (await fetch('/api/system/status')).json();
    const sig = s.signal_state || 'UNKNOWN';
    setPill('sys-signal', 'Signal: ' + sig,
      sig === 'RED' ? 'signal-RED' : sig === 'YELLOW' ? 'signal-YELLOW' : sig === 'GREEN' ? 'signal-GREEN' : 'warn');
    const ard = s.arduino || '?';
    setPill('sys-arduino', 'Arduino: ' + ard, /CONNECTED/.test(ard) ? 'ok' : /DEMO/.test(ard) ? 'warn' : 'bad');
    const cam = s.camera || '?';
    setPill('sys-camera', 'Camera: ' + cam, /CONNECTED/.test(cam) ? 'ok' : 'bad');
    setPill('sys-db', 'DB: ' + (s.database || 'CONNECTED'), 'ok');
    return s;
  } catch (e) {
    setPill('sys-signal', 'Signal: offline', 'bad');
    return null;
  }
}
document.addEventListener('DOMContentLoaded', () => {
  refreshStrip();
  setInterval(refreshStrip, 5000);
  // Feed watchdog: if MJPEG errors, show retry overlay (live page).
  const feed = document.getElementById('feed');
  const off = document.getElementById('feed-off');
  if (feed && off) {
    feed.addEventListener('error', () => off.classList.add('show'));
    feed.addEventListener('load', () => { /* first frame ok */ });
  }
});
async function reloadFeed() {
  const feed = document.getElementById('feed');
  const off = document.getElementById('feed-off');
  if (off) off.classList.remove('show');
  try {
    const cs = await (await fetch('/api/camera/status')).json();
    if (!cs.available) {
      toast('Camera not available: ' + (cs.last_error || cs.source));
      if (off) off.classList.add('show');
      return;
    }
  } catch (e) {}
  if (feed) feed.src = '/api/camera/feed?ts=' + Date.now();
}
