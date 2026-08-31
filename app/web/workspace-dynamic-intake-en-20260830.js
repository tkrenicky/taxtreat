(() => {
  "use strict";

  const previousFetch = window.fetch.bind(window);

  const COPY = {
    ownership_percent: ["What percentage of the Czech payer's share capital is held by the recipient?", "The ownership percentage may determine whether a reduced dividend rate is available."],
    direct_ownership: ["Does the recipient hold the stated interest in the Czech payer directly?", "Some exemptions or reduced treaty rates require direct ownership."],
    direct_or_indirect_voting_ownership: ["What percentage of the voting rights in the Czech payer is held or controlled by the recipient?", "Some treaty dividend thresholds are based on voting rights rather than share capital."],
    holding_period_months: ["From what date has the recipient held the interest in the Czech payer?", "TaxTreat uses the acquisition date to determine the relevant holding period."],
    article_10_public_body_exemption: ["Does the recipient fall within the treaty's qualifying public-body category for the Article 10 dividend exemption?", "Some treaties contain a separate zero-rate dividend branch for a government, central bank or another expressly qualifying public body."],
    article_10_3_public_body_exemption: ["Does the recipient fall within the qualifying public-body category described in Article 10(3)?", "This zero-rate dividend branch applies only to the public bodies expressly covered by the treaty."],
    article_11_public_body_exemption: ["Does this interest fall within the treaty's qualifying public or government-supported exemption under Article 11?", "The exemption applies only if the treaty's specific public-body or government-supported financing conditions are met."],
    article_11_3_public_financing_exemption: ["Does this interest qualify for the public or government-backed financing exemption under Article 11(3)?", "This branch is available only for the public institutions or qualifying government-backed financing expressly covered by the treaty."],
    article_11_3_exemption: ["Does this interest qualify for the special exemption under Article 11(3)?", "The applicable treaty contains a special interest branch whose factual conditions must be confirmed."],
    article_11_3a_exemption: ["Does this interest qualify for the special exemption under Article 11(3)(a)?", "The applicable treaty contains a special interest branch whose factual conditions must be confirmed."],
    special_article_11_3_exemption: ["Does this interest qualify for the treaty's special Article 11(3) exemption?", "The special branch applies only if the conditions stated in the relevant treaty are met."],
    recipient_is_bank: ["Is the interest recipient a bank for purposes of the applicable treaty?", "Some treaties provide a reduced interest rate only to qualifying banks."],
    recipient_is_financial_institution_or_insurer: ["Is the recipient a qualifying financial institution, including an insurer, for purposes of the applicable treaty?", "Some treaties provide a special interest rate only to a qualifying financial institution."],
    recipient_has_share_capital: ["Is the recipient a company whose capital is wholly or partly divided into shares for purposes of the applicable treaty?", "Some older treaties condition a dividend exemption on this specific company characteristic."],
    recipient_is_qualifying_pension_fund: ["Is the recipient a qualifying pension fund for purposes of the applicable treaty?", "A qualifying pension fund may fall within a separate treaty dividend branch."],
    recipient_is_central_bank: ["Is the recipient a central bank for purposes of the applicable treaty?", "A central bank may fall within a separate treaty branch."],
    recipient_is_partnership: ["Is the recipient a partnership for purposes of the applicable treaty?", "Some reduced dividend branches expressly exclude partnerships."],
    recipient_has_immediate_entitlement: ["Is the recipient immediately entitled to the royalty income under the applicable treaty rule?", "The treaty branch depends on the recipient's entitlement to the royalty."],
    recipient_taxed_in_residence: ["Is the relevant income subject to tax in the recipient's state of residence as required by the treaty?", "The treaty relief depends on the residence-state taxation condition."],
    recipient_or_financing: ["Do the recipient or the financing arrangement satisfy the treaty's special qualifying category?", "The applicable treaty distinguishes a special interest branch by reference to the recipient or the financing arrangement."],
    recipient_or_loan_provider_or_guarantor: ["Do the recipient, loan provider or guarantor satisfy the treaty's special qualifying category?", "The applicable treaty contains a special interest branch linked to the status of the relevant financing parties."],
    loan_or_credit_provider: ["Does the loan or credit provider fall within the qualifying category specified by the treaty?", "The interest rate depends on the status of the provider under the applicable treaty."],
    loan_provider: ["Does the loan provider fall within the qualifying category specified by the treaty?", "The interest rate depends on the status of the provider under the applicable treaty."],
    lender_category: ["Which treaty category applies to the lender?", "The applicable treaty uses the lender's category to determine the interest treatment."],
    borrower_category: ["Which treaty category applies to the borrower?", "The applicable treaty uses the borrower's category to determine the interest treatment."],
    official_foreign_exchange_reserve_investment: ["Is the interest connected with an investment of official foreign-exchange reserves covered by the treaty?", "The treaty contains a special branch for qualifying official reserve investments."],
    purpose: ["Does the financing have the purpose required by the applicable treaty branch?", "The treaty's special interest treatment depends on the purpose of the financing."],
    qualifying_article_11_2a_case: ["Does the interest fall within the qualifying case described in Article 11(2)(a)?", "The applicable treaty provides a separate interest treatment for this specific category."],
    loan_is_noncommercial: ["Is the loan non-commercial within the meaning of the applicable treaty?", "The treaty distinguishes this category from ordinary commercial financing."],
    minimum_loan_term_years: ["Does the financing satisfy the minimum term required by the applicable treaty?", "The special treaty branch is available only if the financing term meets the stated threshold."],
    recipient_country_royalty_wht: ["Does the residence-state royalty-tax condition required by the treaty apply?", "The treaty branch depends on the specified residence-state royalty taxation condition."],
    detailed_eligibility_review_required: ["A detailed treaty eligibility review is required for this branch.", "This condition cannot be reduced to a single factual confirmation without reviewing the relevant legal and transaction documents."],
    distributed_vs_undistributed_corporate_tax_rate_difference: ["Does the relevant corporate-tax-rate difference meet the treaty threshold?", "The applicable dividend rule depends on the specified difference between the taxation of distributed and undistributed profits."],
  };

  const LABELS = {
    beneficial_owner: "beneficial ownership of the income",
    recipient_is_treaty_resident: "treaty residence of the recipient",
    permanent_establishment_connection: "connection with a Czech permanent establishment",
    arm_length_amount: "arm's-length amount",
    payment_is_arm_length_amount: "arm's-length amount",
    recipient_entity_type: "recipient entity type",
    royalty_category: "royalty category",
    general_article_11_2_rate: "general Article 11(2) rate",
    source_state_taxation: "source-state taxation condition",
  };

  function isEnglish() {
    return document.documentElement.lang === "en" || window.__TAXTREAT_LOCALE__ === "en";
  }

  function factFromQuestion(question) {
    const path = String(question?.input_path || "");
    return path.startsWith("facts.") ? path.slice(6) : "";
  }

  function humanize(fact) {
    if (LABELS[fact]) return LABELS[fact];
    return String(fact || "")
      .replace(/^article_(\d+)_/i, "Article $1 ")
      .replace(/_(\d+)([a-z])_/gi, " $1($2) ")
      .replace(/_/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function copyFor(question) {
    const fact = factFromQuestion(question);
    if (!fact) return null;
    if (COPY[fact]) return COPY[fact];
    const label = humanize(fact) || "the required treaty fact";
    return [
      `Please confirm the following treaty fact: ${label}.`,
      "This fact is required to determine which branch of the applicable treaty rule applies to the transaction.",
    ];
  }

  function localizeIntake(body) {
    const questions = body?.intake?.questions;
    if (!Array.isArray(questions)) return body;
    questions.forEach((question) => {
      const copy = copyFor(question);
      if (!copy) return;
      question.prompt = copy[0];
      question.why = copy[1];
    });
    return body;
  }

  window.fetch = async function taxTreatConditionAwareEnglishFetch(resource, options = {}) {
    const response = await previousFetch(resource, options);
    const url = typeof resource === "string" ? resource : resource?.url || "";
    if (!isEnglish() || !url.includes("/analysis/intake") || !response.ok) return response;
    try {
      const body = localizeIntake(await response.clone().json());
      const headers = new Headers(response.headers);
      headers.set("content-type", "application/json; charset=utf-8");
      return new Response(JSON.stringify(body), {
        status: response.status,
        statusText: response.statusText,
        headers,
      });
    } catch (_problem) {
      return response;
    }
  };
})();
