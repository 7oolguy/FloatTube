/* Native playback only: no canvas, stream capture, or second player. */
(() => {
  "use strict";
  async function toggle(video, doc = document) {
    if (!video || video.readyState < 1) throw new Error("Start a YouTube video first, then try again.");
    if (typeof video.webkitSupportsPresentationMode === "function" &&
        typeof video.webkitSetPresentationMode === "function" &&
        video.webkitSupportsPresentationMode("picture-in-picture")) {
      video.webkitSetPresentationMode(video.webkitPresentationMode === "picture-in-picture" ? "inline" : "picture-in-picture");
      return;
    }
    if (doc.pictureInPictureElement) {
      await doc.exitPictureInPicture();
      return;
    }
    if (doc.pictureInPictureEnabled && typeof video.requestPictureInPicture === "function") {
      await video.requestPictureInPicture();
      return;
    }
    throw new Error("Picture in Picture is unavailable for this video in this Safari version.");
  }
  globalThis.FloatTube = Object.freeze({ toggle });
})();
