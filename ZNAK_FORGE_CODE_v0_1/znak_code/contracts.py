"""Serializable contracts used by the engine and providers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RunState(str, Enum):
    BOOT = "BOOT"
    ORIENT = "ORIENT"
    BASELINE = "BASELINE"
    REQUIREMENT_RECOVERY = "REQUIREMENT_RECOVERY"
    LOCALIZE = "LOCALIZE"
    HYPOTHESIS = "HYPOTHESIS"
    PATCH_PLAN = "PATCH_PLAN"
    MUTATION_GATE = "MUTATION_GATE"
    APPLY = "APPLY"
    VERIFY_FUNCTIONAL = "VERIFY_FUNCTIONAL"
    VERIFY_CONTRACT = "VERIFY_CONTRACT"
    VERIFY_SHADOW = "VERIFY_SHADOW"
    FINAL_REVIEW = "FINAL_REVIEW"
    ACCEPTED = "ACCEPTED"
    ROLLBACK = "ROLLBACK"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class ClaimType(str, Enum):
    FACT = "FACT"
    EXECUTED_RESULT = "EXECUTED_RESULT"
    EVIDENCE = "EVIDENCE"
    INFERENCE = "INFERENCE"
    HYPOTHESIS = "HYPOTHESIS"
    CLAIMED = "CLAIMED"
    UNKNOWN = "UNKNOWN"
    BLOCKED = "BLOCKED"


@dataclass
class TaskContract:
    goal: str
    explicit_requirements: List[str] = field(default_factory=list)
    implicit_requirement_candidates: List[str] = field(default_factory=list)
    exclusions: List[str] = field(default_factory=list)
    acceptance_conditions: List[str] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "TaskContract":
        fields = cls.__dataclass_fields__
        return cls(**{key: value[key] for key in fields if key in value})


@dataclass
class EvidenceItem:
    evidence_id: str
    source: str
    locator: str
    kind: str
    claim: str
    supports: List[str] = field(default_factory=list)
    contradicts: List[str] = field(default_factory=list)
    sha256: str = ""
    observed_at: str = ""
    claim_type: str = ClaimType.EVIDENCE.value

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def carries_semantic_evidence(self) -> bool:
        """A hash is identity evidence, never proof that content is correct."""
        return bool(self.claim.strip()) and self.kind.upper() not in {"HASH", "CHECKSUM"}


@dataclass
class LocalizationProof:
    target_file: str
    target_symbol_or_region: str
    failure_or_requirement: str
    evidence_refs: List[str]
    dependency_neighbors: List[str]
    why_this_location: str
    why_not_obvious_alternatives: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def complete(self) -> bool:
        scalar = (
            self.target_file,
            self.target_symbol_or_region,
            self.failure_or_requirement,
            self.why_this_location,
            self.why_not_obvious_alternatives,
        )
        return all(part.strip() for part in scalar) and bool(self.evidence_refs)


@dataclass
class Hypothesis:
    hypothesis_id: str
    statement: str
    evidence_for: List[str]
    evidence_against: List[str]
    falsifier: str
    expected_observation_if_true: str
    status: str = "OPEN"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChangeBudget:
    max_files: int = 3
    max_new_files: int = 1
    max_changed_functions: int = 5
    max_changed_loc: int = 120

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PatchItem:
    patch_item_id: str
    target: str
    requirement_refs: List[str]
    evidence_refs: List[str]
    hypothesis_ref: str
    expected_effect: str
    risk: str
    verification_refs: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FileChange:
    target: str
    content: str
    expected_sha256: str = ""
    changed_functions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationSpec:
    verification_id: str
    kind: str
    argv: List[str]
    requirement_refs: List[str] = field(default_factory=list)
    timeout_seconds: int = 60

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PatchPlan:
    items: List[PatchItem]
    changes: List[FileChange]
    verifications: List[VerificationSpec]
    budget: ChangeBudget = field(default_factory=ChangeBudget)
    abstraction_tax: List[Dict[str, str]] = field(default_factory=list)
    syntax_commands: List[List[str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items],
            "changes": [change.to_dict() for change in self.changes],
            "verifications": [item.to_dict() for item in self.verifications],
            "budget": self.budget.to_dict(),
            "abstraction_tax": self.abstraction_tax,
            "syntax_commands": self.syntax_commands,
        }

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "PatchPlan":
        return cls(
            items=[PatchItem(**item) for item in value.get("items", [])],
            changes=[FileChange(**item) for item in value.get("changes", [])],
            verifications=[VerificationSpec(**item) for item in value.get("verifications", [])],
            budget=ChangeBudget(**value.get("budget", {})),
            abstraction_tax=value.get("abstraction_tax", []),
            syntax_commands=value.get("syntax_commands", []),
        )


@dataclass
class BrainRequest:
    task: Dict[str, Any]
    baseline: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    authorized_repository: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BrainResponse:
    evidence: List[EvidenceItem] = field(default_factory=list)
    localization: Optional[LocalizationProof] = None
    hypotheses: List[Hypothesis] = field(default_factory=list)
    patch_plan: Optional[PatchPlan] = None
    unknowns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence": [item.to_dict() for item in self.evidence],
            "localization": self.localization.to_dict() if self.localization else None,
            "hypotheses": [item.to_dict() for item in self.hypotheses],
            "patch_plan": self.patch_plan.to_dict() if self.patch_plan else None,
            "unknowns": self.unknowns,
        }

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "BrainResponse":
        localization = value.get("localization")
        plan = value.get("patch_plan")
        return cls(
            evidence=[EvidenceItem(**item) for item in value.get("evidence", [])],
            localization=LocalizationProof(**localization) if localization else None,
            hypotheses=[Hypothesis(**item) for item in value.get("hypotheses", [])],
            patch_plan=PatchPlan.from_dict(plan) if plan else None,
            unknowns=value.get("unknowns", []),
        )


@dataclass
class GateDecision:
    allow: bool
    reason: str
    details: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

