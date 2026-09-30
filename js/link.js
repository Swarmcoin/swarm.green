/* /u, /g, /stickers: hand a SWARM Messenger link to the app.
   The app makes three kinds of share links on this site:
     https://swarm.green/u/#eu/<encrypted username>
     https://swarm.green/g/#<group invitation>
     https://swarm.green/stickers/#pack_id=<id>&pack_key=<key>
   Everything that matters sits in the fragment, which browsers never send to
   a server, and this script sends nothing either: it copies the fragment onto
   the button's swarm:// address, the form the app opens. When the fragment is
   missing or not in the shape of its kind, the note replaces the button. The
   strict CSP allows no inline script, so these lines live in their own file. */
(function () {
  "use strict";
  var open = document.querySelector("[data-link-open]");
  var missing = document.querySelector("[data-link-missing]");
  var link = document.querySelector("[data-link-app]");
  if (!open || !missing || !link) return;
  var kind = link.getAttribute("data-link-app");
  var hash = window.location.hash;
  var rest = hash.slice(1);
  var complete = false;
  if (kind === "u") {
    complete = /^(eu|p)\/[^\/]+$/.test(rest);
  } else if (kind === "g") {
    complete = /^[^\/]+$/.test(rest);
  } else if (kind === "stickers") {
    var params = new URLSearchParams(rest);
    complete = Boolean(params.get("pack_id") && params.get("pack_key"));
  }
  if (complete) {
    link.href = "swarm://swarm.green/" + kind + "/" + hash;
    open.hidden = false;
    missing.remove();
  } else {
    missing.hidden = false;
    open.remove();
  }
}());
