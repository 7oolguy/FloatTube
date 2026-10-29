(() => {
  "use strict";
  if (globalThis.__floatTubeInstalled) return;
  globalThis.__floatTubeInstalled = true;
  const button = document.createElement("button");
  button.className = "ytp-button floattube-button";
  button.type = "button";
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 36 36");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", "M29 9H7v18h22V9zm-2 16H9V11h18v14zm-11-9h9v7h-9v-7z");
  svg.append(path);
  button.append(svg);
  button.title = document.documentElement.lang.startsWith("pt") ? "Picture-in-picture" : "Picture in picture";
  button.setAttribute("aria-label", "Open or close Picture in Picture");
  const status = document.createElement("div");
  status.className = "floattube-status";
  status.setAttribute("role", "status");
  let dismiss;
  function showError(message) {
    status.textContent = message;
    document.body.append(status);
    clearTimeout(dismiss);
    dismiss = setTimeout(() => status.remove(), 6000);
  }
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    // Keep the native call in the actual click's user-activation context.
    const video = document.querySelector("#movie_player video") || document.querySelector("video");
    FloatTube.toggle(video).catch(error => showError(error.message || "Could not open Picture in Picture."));
  });
  function attach() {
    const controls = document.querySelector("#movie_player .ytp-right-controls") || document.querySelector(".ytp-right-controls");
    if (controls && button.parentElement !== controls) controls.prepend(button);
  }
  let scheduled = false;
  const observer = new MutationObserver(() => {
    if (scheduled || button.isConnected) return;
    scheduled = true;
    queueMicrotask(() => { scheduled = false; attach(); });
  });
  attach();
  // Child-list only; no layout reads, recurring timers, or attribute observation.
  observer.observe(document.body, { childList: true, subtree: true });
  window.addEventListener("pagehide", () => { observer.disconnect(); clearTimeout(dismiss); });
  window.addEventListener("pageshow", event => {
    if (event.persisted) { attach(); observer.observe(document.body, { childList: true, subtree: true }); }
  });
})();
