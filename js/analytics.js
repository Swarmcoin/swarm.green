/* Google Analytics 4 for swarm.green, measurement id G-3MDDZNCW6P.
   These are the lines of Google's tag that would normally sit inline in the
   page; the strict CSP allows no inline script, so they live in their own
   file, loaded right after gtag.js. Every page loads the two except /call,
   /u, /g and /stickers: those carry a key or an invitation after #, and
   nothing on them may go to a third party. For the same reason the page
   address is sent without the part after #, and on /waitlist without the
   query too: "?i=" there is a person's invite code, which stays with us.
   No event anywhere carries an email or a SWARM address.
   /privacy says what is collected. */
window.dataLayer = window.dataLayer || [];
function gtag() { dataLayer.push(arguments); }
gtag("js", new Date());
gtag("config", "G-3MDDZNCW6P", {
  page_location: window.location.origin + window.location.pathname
    + (window.location.pathname === "/waitlist" ? "" : window.location.search)
});
