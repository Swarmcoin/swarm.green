/* Progressive enhancement: all platform downloads remain usable without JS. */
(function () {
  "use strict";
  var picker = document.querySelector("[data-platform-picker]");
  if (!picker) return;
  var buttons = Array.from(picker.querySelectorAll("[data-platform]"));
  var panels = Array.from(document.querySelectorAll("[data-platform-panel]"));
  function choose(platform) {
    buttons.forEach(function (button) {
      button.setAttribute("aria-pressed", String(button.dataset.platform === platform));
    });
    panels.forEach(function (panel) {
      panel.hidden = panel.dataset.platformPanel !== platform;
    });
  }
  picker.addEventListener("click", function (event) {
    var button = event.target.closest("[data-platform]");
    if (button) choose(button.dataset.platform);
  });
  var ua = navigator.userAgent;
  var platform = /Android/i.test(ua) ? "android" : /iPhone|iPad/i.test(ua) ? "iphone" : /Mac/i.test(ua) ? "macos" : /Linux/i.test(ua) ? "linux" : "windows";
  if (!buttons.some(function (b) { return b.dataset.platform === platform; })) platform = "windows";
  choose(platform);
  picker.hidden = false;
}());
