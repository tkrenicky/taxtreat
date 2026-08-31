(() => {
  "use strict";

  function apply() {
    const width = window.innerWidth || 1440;
    const size = width <= 1080 ? "16px" : width <= 1320 ? "17px" : "18px";
    document.querySelectorAll('.app-header nav button[data-nav]').forEach((button) => {
      button.style.setProperty("font-size", size, "important");
      button.style.setProperty("font-weight", "700", "important");
      button.style.setProperty("line-height", "1.1", "important");
      button.style.setProperty("letter-spacing", "-0.01em", "important");
    });
  }

  apply();
  document.addEventListener("click", (event) => {
    if (event.target?.closest?.("[data-nav],#taxtreat-language-controls")) {
      window.setTimeout(apply, 0);
      window.setTimeout(apply, 120);
    }
  }, true);
  window.addEventListener("resize", () => window.setTimeout(apply, 50));
})();
