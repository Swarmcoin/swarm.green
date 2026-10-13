(() => {
  'use strict';
  const consoleEl = document.querySelector('[data-download-console]');
  if (!consoleEl) return;
  const products = {
    wallet: { name: 'SWARM Wallet', line: 'YOUR KEYS. YOUR SWM.', text: 'Hold, send and receive native SWM. Choose shielded or transparent payments, with your keys kept on your device.', route: '/ecosystem/wallet', badge: 'DESKTOP WALLET' },
    messenger: { name: 'SWARM Messenger', line: 'CONVERSATIONS. WITH PAYMENTS.', text: 'End-to-end encrypted desktop messages, with your SWARM wallet and payments in the conversation. An early, unsigned release.', route: '/ecosystem/messenger', badge: 'DESKTOP PRE-RELEASE' },
    browser: { name: 'SWARM Browser', line: 'YOUR WALLET. IN YOUR BROWSER.', text: 'A Chromium-based Windows browser with Google’s services removed and the SWARM wallet in its toolbar. An early, unsigned release.', route: '/ecosystem/browser', badge: 'WINDOWS PRE-RELEASE' }
  };
  const tabs = [...document.querySelectorAll('[data-product]')];
  const osButtons = [...document.querySelectorAll('[data-os]')];
  const panel = document.querySelector('[data-product-panel]');
  const result = document.querySelector('[data-download-result]');
  const archWrap = document.querySelector('[data-architecture]');
  const arch = document.querySelector('#download-architecture');
  const status = document.querySelector('[data-download-status]');
  const suggestion = document.querySelector('[data-os-suggestion]');
  const detected = /Windows/i.test(navigator.userAgent) ? 'Windows' : /Macintosh|Mac OS X/i.test(navigator.userAgent) && !/iPhone|iPad/i.test(navigator.userAgent) ? 'macOS' : /Linux/i.test(navigator.userAgent) && !/Android/i.test(navigator.userAgent) ? 'Linux' : null;
  let productKey = 'wallet', selectedOS = detected || 'Windows';
  let entries = [], meta = {};
  const el = (tag, className, text) => { const n = document.createElement(tag); if (className) n.className = className; if (text) n.textContent = text; return n; };
  const link = (text, url, className) => { const n = el('a', className, text); n.href = url; return n; };
  const family = row => row.platform.startsWith('macOS') ? 'macOS' : row.platform;
  function render() {
    const product = products[productKey];
    tabs.forEach(tab => { const active = tab.dataset.product === productKey; tab.setAttribute('aria-selected', String(active)); tab.tabIndex = active ? 0 : -1; });
    osButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.os === selectedOS)));
    panel.setAttribute('aria-labelledby', 'product-' + productKey);
    document.querySelector('[data-product-name]').textContent = product.name;
    document.querySelector('[data-product-line]').textContent = product.line;
    document.querySelector('[data-product-description]').textContent = product.text;
    const guide = document.querySelector('[data-product-guide]'); guide.href = product.route;
    suggestion.textContent = detected && selectedOS === detected ? 'Suggested for this device' : '';
    archWrap.hidden = selectedOS !== 'macOS';
    const chosenPlatform = selectedOS === 'macOS' ? 'macOS (' + arch.value + ')' : selectedOS;
    const files = entries.filter(row => row.product === productKey && row.platform === chosenPlatform);
    const primary = files.find(row => row.role === 'primary') || files[0];
    result.replaceChildren();
    if (!primary) {
      const empty = el('div', 'download-unavailable');
      empty.append(el('h3', '', 'No ' + chosenPlatform + ' build yet.'));
      const available = [...new Set(entries.filter(row => row.product === productKey).map(row => row.platform))].join(', ');
      empty.append(el('p', '', available ? 'Published platforms: ' + available + '. Choose a supported system above.' : 'A current download has not been published.'));
      empty.append(link('View product details →', product.route, 'dv-textlink'));
      result.append(empty);
      status.textContent = product.name + ': no ' + chosenPlatform + ' build is published.';
      return;
    }
    const primaryBox = el('div', 'download-primary');
    primaryBox.append(link('Download for ' + selectedOS + ' ↓', primary.url, 'rd-button rd-button-primary'));
    primaryBox.append(el('p', 'download-version', primary.version + ' · ' + primary.variant + ' · ' + primary.sizeShort));
    let notice = 'Compare the SHA-256 before installing.';
    if (selectedOS === 'Windows') notice = 'Unsigned build. Windows SmartScreen may warn. Verify the file before installing.';
    if (selectedOS === 'macOS' && /not signed|unsigned/i.test(primary.notes || '')) notice = 'Unsigned and not notarized by Apple. Read the install guide and verify the file before opening.';
    primaryBox.append(el('p', 'download-notice', notice));
    result.append(primaryBox);
    const details = el('details', 'download-secondary');
    details.append(el('summary', '', 'Verify file & other download formats'));
    const hash = el('p', '', 'SHA-256 · ' + primary.variant); hash.append(el('code', '', primary.sha256)); details.append(hash);
    const verify = el('p'); verify.append(link('Published checksums', primary.checksums), document.createTextNode(' · '), link('How to verify', '/verify')); details.append(verify);
    files.filter(row => row !== primary).forEach(row => {
      details.append(link(row.variant + ' · ' + row.sizeShort + ' ↓', row.url, 'download-alt'));
      const altHash = el('p', '', 'SHA-256 · ' + row.variant); altHash.append(el('code', '', row.sha256)); details.append(altHash);
    });
    const records = el('p'); records.append(link('Installation guide', product.route), document.createTextNode(' · '), link('Release records', meta.releasesUrl)); details.append(records);
    result.append(details);
    status.textContent = product.name + ' for ' + chosenPlatform + ', version ' + primary.version + ', ready to download.';
  }
  fetch('/data/downloads.json', { cache: 'no-cache' }).then(response => { if (!response.ok) throw new Error('Downloads unavailable'); return response.json(); }).then(data => {
    meta = data.meta;
    entries = data.entries.filter(row => row.status === 'available' && !row.paused && row.channel !== 'testnet' && row.url && !(meta.unavailableHosts || []).some(host => row.url.startsWith(host)) && /^[a-f0-9]{64}$/i.test(row.sha256 || '') && row.sizeBytes > 0 && row.checksums);
    document.querySelector('[data-download-fallback]').hidden = true;
    document.querySelector('[data-download-interactive]').hidden = false;
    document.querySelector('[data-download-tabs]').hidden = false;
    render();
    tabs.forEach(tab => tab.addEventListener('click', () => { productKey = tab.dataset.product; render(); }));
    document.querySelector('[data-download-tabs]').addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      let index = tabs.indexOf(document.activeElement);
      if (index < 0) return;
      index = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
      productKey = tabs[index].dataset.product; render(); tabs[index].focus();
    });
    osButtons.forEach(button => button.addEventListener('click', () => { selectedOS = button.dataset.os; render(); }));
    arch.addEventListener('change', render);
  }).catch(() => { status.textContent = 'Use the product guides below to find your download.'; });
})();
