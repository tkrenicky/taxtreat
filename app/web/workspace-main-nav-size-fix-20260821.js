(() => {
  "use strict";

  if (document.querySelector("#tt-main-nav-size-fix-20260821")) return;

  const style = document.createElement("style");
  style.id = "tt-main-nav-size-fix-20260821";
  style.textContent = `
    /* Main navigation tiles — intentionally and visibly larger. */
    .app-header nav {
      display:flex!important;
      align-items:center!important;
      gap:10px!important;
    }

    .app-header nav button[data-nav] {
      min-height:56px!important;
      min-width:112px!important;
      padding:0 22px!important;
      border-radius:12px!important;
      font-size:19px!important;
      line-height:1!important;
      font-weight:760!important;
      letter-spacing:-0.01em!important;
    }

    .app-header nav button[data-nav].active {
      background:rgba(255,255,255,.14)!important;
      box-shadow:inset 0 -3px 0 rgba(255,255,255,.95)!important;
    }

    @media (max-width:1180px) {
      .app-header nav { gap:7px!important; }
      .app-header nav button[data-nav] {
        min-width:98px!important;
        min-height:52px!important;
        padding:0 17px!important;
        font-size:18px!important;
      }
    }

    @media (max-width:980px) {
      .app-header nav button[data-nav] {
        min-width:0!important;
        min-height:48px!important;
        padding:0 13px!important;
        font-size:17px!important;
      }
    }
  `;

  document.head.append(style);
})();
