/* The home page video. Until the visitor presses play only a picture from this
   site is shown; the press swaps in the YouTube player (youtube-nocookie.com).
   Without JavaScript the picture is a plain link to the video on YouTube. */
(function () {
  "use strict";
  document.querySelectorAll("a[data-video]").forEach(function (link) {
    link.addEventListener("click", function (event) {
      if (event.ctrlKey || event.metaKey || event.shiftKey) { return; }
      event.preventDefault();
      var frame = document.createElement("iframe");
      frame.className = "video__frame";
      frame.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(link.getAttribute("data-video")) + "?autoplay=1&rel=0";
      frame.title = link.getAttribute("data-video-title") || "Video";
      frame.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
      frame.allowFullscreen = true;
      frame.referrerPolicy = "strict-origin-when-cross-origin";
      link.parentNode.replaceChild(frame, link);
      frame.focus();
    });
  });
})();
