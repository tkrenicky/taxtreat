(() => {
  "use strict";

  const CS_SENTENCE = "Česká srážková daň se proto neuplatní z důvodu osvobození podle § 19 ZDP.";
  const EN_SENTENCE = "Czech withholding tax therefore does not apply because the dividend is exempt under Section 19 of the Czech Income Taxes Act.";

  function language() {
    return document.querySelector("#taxtreat-ui-language")?.value || localStorage.getItem("taxtreat-ui-language") || "cs";
  }

  function section19Applies(box) {
    if (!box) return false;
    const text = box.textContent || "";
    return /§\s*19 ZDP se použije|Section 19 applies|Osvobozeno|Exempt/i.test(text);
  }

  function patch() {
    const box = document.querySelector("#cz-section19-result");
    if (!box || !section19Applies(box)) return;

    const en = language() === "en";
    let paragraph = box.querySelector("p");
    if (!paragraph) {
      paragraph = document.createElement("p");
      box.append(paragraph);
    }

    paragraph.textContent = en ? EN_SENTENCE : CS_SENTENCE;

    // An exemption is a tax treatment, not a 0% statutory/treaty rate.
    box.querySelectorAll("strong,b,span,div").forEach((el) => {
      const value = el.textContent?.trim();
      if (value === "0 %" || value === "0%") {
        el.textContent = en ? "Exempt" : "Osvobozeno";
      }
    });
  }

  document.addEventListener("click", () => window.setTimeout(patch, 0), true);
  document.addEventListener("change", () => window.setTimeout(patch, 0), true);
  window.addEventListener("popstate", () => window.setTimeout(patch, 0));
  window.setTimeout(patch, 0);
})();
