/* /call: hands a SWARM Messenger call link to the app.
   A call link is https://swarm.green/call/#key=<key>. The key sits in the
   fragment, which browsers never send to a server, and this script sends
   nothing either: it copies the fragment onto the button's swarm:// address,
   the form the app opens. Without a key the note replaces the button. The
   strict CSP allows no inline script, so these lines live in their own file. */
(function () {
  "use strict";
  var open = document.querySelector("[data-call-open]");
  var missing = document.querySelector("[data-call-missing]");
  var link = document.querySelector("[data-call-link]");
  if (!open || !missing || !link) return;
  var hash = window.location.hash;
  if (new URLSearchParams(hash.slice(1)).get("key")) {
    link.href = "swarm://swarm.green/call/" + hash;
    open.hidden = false;
    missing.remove();
  } else {
    missing.hidden = false;
    open.remove();
  }
}());
