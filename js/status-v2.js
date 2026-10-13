/* Public-opening countdown follows the published network manifest, not assumed launch state. */
(() => {
  'use strict';
  const targets = [...document.querySelectorAll('[data-opening-countdown]')];
  if (!targets.length) return;
  const fallback = '2026-11-01T15:42:00Z';
  let opening = new Date(fallback).getTime();
  let confirmedOpen = false;
  function render() {
    const seconds = Math.max(0, Math.floor((opening - Date.now()) / 1000));
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor(seconds % 86400 / 3600);
    const minutes = Math.floor(seconds % 3600 / 60);
    const left = seconds % 60;
    const label = seconds ? `${String(days).padStart(2,'0')}d ${String(hours).padStart(2,'0')}h ${String(minutes).padStart(2,'0')}m ${String(left).padStart(2,'0')}s`
      : confirmedOpen ? 'Public mining is open' : 'Scheduled time reached · check network status';
    for (const target of targets) {
      target.textContent = label;
      target.setAttribute('aria-label', seconds ? `Public mining scheduled in ${days} days, ${hours} hours, ${minutes} minutes` : label);
    }
  }
  fetch('/data/network.json', {cache:'no-cache'})
    .then(response => response.ok ? response.json() : Promise.reject())
    .then(data => {
      const date = new Date(data.closedStart?.untilUtc).getTime();
      if (Number.isFinite(date)) opening = date;
      confirmedOpen = data.closedStart?.opened === true;
      render();
    }).catch(() => {});
  render();
  let timer;
  function schedule() {
    clearInterval(timer);
    if (!document.hidden) { render(); timer = setInterval(render,1000); }
  }
  document.addEventListener('visibilitychange',schedule);
  schedule();
})();
