from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


PPT_REPRESENTATION_TEXT = (
    "I confirm, for the purpose of this treaty research, that obtaining the "
    "treaty benefit was not one of the principal purposes of the transaction "
    "or arrangement in circumstances where granting that benefit would be "
    "contrary to the object and purpose of the relevant treaty provisions."
)


class PPTRepresentation(str, Enum):
    CONFIRMED = "confirmed"
    NOT_CONFIRMED = "not_confirmed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PPTTreatment:
    ppt_relevant: bool
    representation_requested: bool
    representation: str | None
    research_may_proceed: bool
    research_basis: str
    treaty_benefit_treatment: str
    separate_anti_abuse_assessment_required: bool
    tax_treat_determined_ppt_satisfied: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def assess_ppt_representation(
    *,
    ppt_relevant: bool,
    representation: PPTRepresentation | str | None = None,
) -> PPTTreatment:
    """Apply the narrow product treatment for PPT without deciding treaty abuse.

    Research evidence remains available for every response.  Confirmation changes
    only the stated basis on which the research may be used; it is never converted
    into a TaxTreat legal determination that the PPT is satisfied.
    """

    if not ppt_relevant:
        if representation not in (None, ""):
            raise ValueError("A PPT representation is not accepted when PPT is irrelevant.")
        return PPTTreatment(
            ppt_relevant=False,
            representation_requested=False,
            representation=None,
            research_may_proceed=True,
            research_basis="ppt_not_applicable_to_country_package",
            treaty_benefit_treatment="subject_to_other_treaty_and_domestic_conditions",
            separate_anti_abuse_assessment_required=False,
            tax_treat_determined_ppt_satisfied=False,
        )

    try:
        value = PPTRepresentation(representation or PPTRepresentation.UNKNOWN)
    except ValueError as exc:
        raise ValueError("Unsupported PPT representation response.") from exc

    confirmed = value is PPTRepresentation.CONFIRMED
    return PPTTreatment(
        ppt_relevant=True,
        representation_requested=True,
        representation=value.value,
        research_may_proceed=True,
        research_basis=(
            "user_representation_confirmed"
            if confirmed
            else "no_user_anti_abuse_assurance"
        ),
        treaty_benefit_treatment=(
            "research_result_subject_to_user_representation_and_other_conditions"
            if confirmed
            else "research_result_retained_but_treaty_benefit_subject_to_separate_ppt_assessment"
        ),
        separate_anti_abuse_assessment_required=not confirmed,
        tax_treat_determined_ppt_satisfied=False,
    )
