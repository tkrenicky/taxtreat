# Slovakia outbound WHT — first human review

Status: **3 review-ready / 6 pilot scopes**  
Runtime: **fail-closed / not released**  
Human approvals recorded: **0**

This worksheet is for independent human legal review. `review-ready` means that the legal chain needed for the questions below has been assembled; it does **not** mean approved or production-released.

## 1. SK → US — dividend — READY FOR HUMAN REVIEW

**Primary treaty:** 74/1994 Z. z., Article 10  
**MLI:** not listed as modified

### Candidate conclusion

For a dividend paid by a Slovak company to a U.S. treaty resident that is the beneficial owner:

- **5%** source-state treaty cap if the beneficial owner is a company owning at least **10% of the voting shares** of the payer;
- **15%** in the other ordinary Article 10 cases.

This conclusion is not unconditional. Article 10 contains special treatment for U.S. Regulated Investment Companies and Real Estate Investment Trusts, and the dividend cap does not apply where the dividend is effectively connected with a source-state PE/fixed base.

### Human review

- [ ] Confirm 5% / 15% Article 10 rate structure.
- [ ] Confirm the 10% voting-right threshold.
- [ ] Confirm RIC/REIT exceptions are modelled correctly.
- [ ] Confirm PE-connection carve-out.
- [ ] Confirm interaction with the current Slovak domestic corporate-dividend treatment before release.

Reviewer outcome: `APPROVE / CORRECT / ISSUE`  
Notes:

---

## 2. SK → NZ — dividend — READY FOR HUMAN REVIEW

**Primary treaty:** 243/2024 Z. z., Article 10  
**MLI:** not listed as modified; BEPS-style provisions are already embedded in the modern base treaty

### Candidate conclusion

For a dividend paid by a Slovak company to a New Zealand treaty resident that is the beneficial owner:

- **5%** source-state treaty cap if the beneficial owner is a company with at least **10% direct voting ownership** throughout a **365-day period including the payment date**; qualifying reorganisation-driven changes are disregarded for this period;
- **15%** in other Article 10 cases.

The Article 10 cap does not apply where the participation is effectively connected with a Slovak PE; Article 7 then governs.

### Human review

- [ ] Confirm 5% / 15% Article 10 rate structure.
- [ ] Confirm 10% direct voting-right threshold.
- [ ] Confirm exact 365-day holding-period rule and reorganisation exception.
- [ ] Confirm PE-connection carve-out.
- [ ] Confirm that treaty-level transparent-entity / anti-abuse conditions are represented even though the treaty is not MLI-listed.
- [ ] Confirm interaction with current Slovak domestic corporate-dividend treatment before release.

Reviewer outcome: `APPROVE / CORRECT / ISSUE`  
Notes:

---

## 3. SK → AT — interest — READY FOR HUMAN REVIEW

**Primary treaty:** 48/1979 Zb., Article 11  
**MLI notice:** 410/2018 Z. z.  
**MLI WHT effective date:** 1 January 2019

### Base-treaty candidate conclusion

In the ordinary Article 11 case, interest sourced in Slovakia and paid to an Austrian treaty resident is taxable **only in Austria**, i.e. the ordinary Slovak source-state treaty rate is **0%**.

The base treaty already removes the Article 11 rule where the interest claim is effectively connected with a Slovak PE/fixed base.

### MLI modifiers that can change the conclusion

The 0% result must **not** be presented as unconditional. The pair-specific Slovak MLI notice introduces relevant safeguards including:

- **Article 7 PPT** — may deny the treaty benefit;
- **Article 10 third-jurisdiction PE rule** — may deny treaty benefits for qualifying low-tax third-state PE structures, after which Slovakia may tax under domestic law, subject to the active-business exception and competent-authority relief mechanism;
- **Article 13 PE-specific-activity changes** — can affect whether a PE exists and therefore whether Article 11 remains applicable;
- **Article 15 closely-related-enterprise definition** — supports the MLI PE rules.

Austria is also an EU jurisdiction, so the Slovak domestic implementation of the Interest and Royalties Directive must be tested as a separate potentially more favourable route before the final runtime result is displayed.

### Human review

- [ ] Confirm ordinary Article 11 source-state rate = 0%.
- [ ] Confirm WHT effectiveness of the MLI changes from 1 January 2019.
- [ ] Confirm Article 7 PPT effect.
- [ ] Confirm Article 10 third-jurisdiction PE effect and exceptions.
- [ ] Confirm Article 13 / 15 PE effects are represented at the right point in the decision tree.
- [ ] Confirm Slovak EU interest exemption must be evaluated as a separate relief route.
- [ ] Confirm domestic fallback logic if treaty benefit is denied.

Reviewer outcome: `APPROVE / CORRECT / ISSUE`  
Notes:

---

# Still blocked — do not review yet

## SK → AU — royalty

Pending completion of the official base Article 12 primary-source chain and full scope-specific matching of 408/2018 Z. z.

## SK → NL — royalty

Pending confirmation of operative Article 12 after protocols 199/1997 and 450/2010 and completion of the royalty-specific MLI overlay under 486/2019 Z. z.

## SK → GB — interest

Pending ingestion of the corrected 89/1992 wording after 420/2023, territorial-scope resolution, and substantive interest-specific MLI matching under 412/2018 Z. z.
