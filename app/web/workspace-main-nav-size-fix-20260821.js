(() => {
  "use strict";

  if (document.querySelector("#tt-main-nav-size-fix-20260821")) return;

  const style = document.createElement("style");
  style.id = "tt-main-nav-size-fix-20260821";
  style.textContent = `
    /* Main navigation tiles — keep the tiles balanced, make the LABELS visibly larger. */
    .app-header nav {
      display:flex!important;
      align-items:center!important;
      gap:12px!important;
    }

    .app-header nav button[data-nav] {
      min-height:64px!important;
      min-width:136px!important;
      padding:0 25px!important;
      border-radius:13px!important;
      font-size:30px!important;
      line-height:1!important;
      font-weight:780!important;
      letter-spacing:-0.02em!important;
    }

    .app-header nav button[data-nav].active {
      background:rgba(255,255,255,.15)!important;
      box-shadow:inset 0 -4px 0 rgba(255,255,255,.96)!important;
    }

    @media (max-width:1320px) {
      .app-header nav { gap:9px!important; }
      .app-header nav button[data-nav] {
        min-width:116px!important;
        min-height:60px!important;
        padding:0 20px!important;
        font-size:27px!important;
      }
    }

    @media (max-width:1080px) {
      .app-header nav { gap:6px!important; }
      .app-header nav button[data-nav] {
        min-width:0!important;
        min-height:54px!important;
        padding:0 13px!important;
        font-size:23px!important;
      }
    }
  `;

  document.head.append(style);
})();
