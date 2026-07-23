/* RAPP Brainstem — Brain Surgeon overlay.
 * One <script> line in the brainstem index.html pulls this in. It adds a flat SCALPEL
 * button to the toolbar; clicking it slides in the surgeon pane (a separate Copilot
 * conversation, served by this sidecar) beside the brainstem chat. No other index.html
 * change. In VS Code "advanced mode" the user simply never clicks it and uses their own
 * Copilot instead.
 */
(function () {
  if (window.__brainSurgeonOverlay) return;
  window.__brainSurgeonOverlay = true;

  // Derive the sidecar origin from this script's own src.
  var me = document.currentScript && document.currentScript.src || "";
  var SIDE = me.replace(/\/overlay\.js.*$/, "") || "http://localhost:7072";

  // Flat scalpel icon (filled blade with a rounded spine + slim handle). No emoji.
  var SCALPEL =
    '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" ' +
    'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">' +
    '<path d="M4 20 L11.5 12.5"/>' +
    '<path d="M11.5 12.5 L19 5 a1.8 1.8 0 0 0 -2.5 -2.5 L9 10 Z" fill="currentColor" stroke="none"/>' +
    '</svg>';

  function inject() {
    var controls = document.querySelector("header .controls") || document.querySelector(".controls");
    if (!controls) return setTimeout(inject, 400);
    if (document.getElementById("scalpel-btn")) return;

    var btn = document.createElement("button");
    btn.className = "icon-btn";
    btn.id = "scalpel-btn";
    btn.title = "Brain Surgeon — operate on your agent cartridges (the patient stays awake)";
    btn.innerHTML = '<span class="icon">' + SCALPEL + "</span>";

    var pane = document.createElement("iframe");
    pane.id = "scalpel-pane";
    pane.title = "Brain Surgeon";
    pane.style.cssText =
      "position:fixed;top:0;right:0;width:40%;max-width:660px;height:100vh;border:0;" +
      "border-left:1px solid #30363d;box-shadow:-8px 0 28px rgba(0,0,0,.45);z-index:9999;" +
      "transform:translateX(105%);transition:transform .2s ease;background:#0d1117;";
    document.body.appendChild(pane);

    var open = false;
    btn.onclick = function () {
      open = !open;
      if (open && !pane.src) pane.src = SIDE + "/"; // lazy: don't start the surgeon until summoned
      pane.style.transform = open ? "translateX(0)" : "translateX(105%)";
      btn.classList.toggle("active", open);
    };
    // Sit it just before the gear/settings cluster if possible, else append.
    controls.appendChild(btn);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", inject);
  else inject();
})();
