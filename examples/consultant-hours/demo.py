"""
Reference implementation of the Consultant hours Tundra model.

Implements: models/consultant-hours-invoice.tundra
Language: Python (standard library only)

Demonstrates Roles as actors, separate state per subject (Hours vs Invoice),
fail-fast Contracts, and both happy-path and error Scenarios.
"""

from __future__ import annotations

import sys
from enum import Enum, auto


# ------------------------------------------------------------------
# Roles and states (one state type per subject)
# ------------------------------------------------------------------

class Role(Enum):
    CONSULTANT = auto()
    MANAGER = auto()
    CLIENT = auto()


class HoursState(Enum):
    NONE = auto()
    DRAFT = auto()
    SUBMITTED = auto()
    INVOICED = auto()


class InvoiceState(Enum):
    NONE = auto()
    OPEN = auto()
    APPROVED = auto()
    DISPUTED = auto()


class ContractViolation(Exception):
    """Raised when a Tundra Contract would be broken."""

    def __init__(self, contract: str) -> None:
        self.contract = contract
        super().__init__(contract)


# Contract texts (single source of messages; match the .tundra model)
C_EDIT_DRAFT_ONLY = (
    "Hours may be edited by the Consultant only while they are in Draft"
)
C_INVOICE_FROM_SUBMITTED = (
    "An invoice may be created only from Submitted hours that have not already been invoiced"
)
C_CLIENT_APPROVE_DISPUTE = (
    "Only the Client may Approve or Dispute an open invoice"
)
C_MANAGER_CREATES_INVOICE = (
    "Only the Manager may create an invoice"
)


# ------------------------------------------------------------------
# Processes
# ------------------------------------------------------------------

def register_hours(actor: Role, hours: HoursState) -> HoursState:
    """Consultant registers hours → Hours are in Draft"""
    if actor != Role.CONSULTANT:
        raise ContractViolation(
            "Hours may be registered only by the Consultant"
        )
    if hours != HoursState.NONE:
        raise ContractViolation(
            "Register Hours requires that no hours exist yet"
        )
    return HoursState.DRAFT


def edit_hours(actor: Role, hours: HoursState) -> HoursState:
    """Consultant edits hours → Hours remain in Draft"""
    if actor != Role.CONSULTANT or hours != HoursState.DRAFT:
        raise ContractViolation(C_EDIT_DRAFT_ONLY)
    return HoursState.DRAFT


def submit_hours(actor: Role, hours: HoursState) -> HoursState:
    """Consultant submits hours → Hours are Submitted"""
    if actor != Role.CONSULTANT:
        raise ContractViolation(
            "Submit Hours requires Actor Consultant"
        )
    if hours != HoursState.DRAFT:
        raise ContractViolation(
            "Submit Hours requires Hours are in Draft"
        )
    return HoursState.SUBMITTED


def create_invoice(
    actor: Role, hours: HoursState, invoice: InvoiceState
) -> tuple[HoursState, InvoiceState]:
    """Manager creates invoice → Invoice is Open; Hours are Invoiced"""
    if actor != Role.MANAGER:
        raise ContractViolation(C_MANAGER_CREATES_INVOICE)
    if hours != HoursState.SUBMITTED or invoice != InvoiceState.NONE:
        raise ContractViolation(C_INVOICE_FROM_SUBMITTED)
    return HoursState.INVOICED, InvoiceState.OPEN


def approve_invoice(actor: Role, invoice: InvoiceState) -> InvoiceState:
    """Client approves invoice → Invoice is Approved"""
    if actor != Role.CLIENT:
        raise ContractViolation(C_CLIENT_APPROVE_DISPUTE)
    if invoice != InvoiceState.OPEN:
        raise ContractViolation(C_CLIENT_APPROVE_DISPUTE)
    return InvoiceState.APPROVED


def dispute_invoice(actor: Role, invoice: InvoiceState) -> InvoiceState:
    """Client disputes invoice → Invoice is Disputed"""
    if actor != Role.CLIENT:
        raise ContractViolation(C_CLIENT_APPROVE_DISPUTE)
    if invoice != InvoiceState.OPEN:
        raise ContractViolation(C_CLIENT_APPROVE_DISPUTE)
    return InvoiceState.DISPUTED


def _fmt(hours: HoursState, invoice: InvoiceState) -> str:
    return f"hours={hours.name}, invoice={invoice.name}"


# ------------------------------------------------------------------
# Scenarios
# ------------------------------------------------------------------

def scenario_happy_path() -> None:
    """Happy path – hours submitted and invoice approved"""
    print("=== Scenario: Happy path – hours submitted and invoice approved ===\n")

    hours = HoursState.NONE
    invoice = InvoiceState.NONE

    hours = register_hours(Role.CONSULTANT, hours)
    print(f"After Register Hours  → {_fmt(hours, invoice)}")
    assert hours == HoursState.DRAFT

    hours = submit_hours(Role.CONSULTANT, hours)
    print(f"After Submit Hours    → {_fmt(hours, invoice)}")
    assert hours == HoursState.SUBMITTED

    hours, invoice = create_invoice(Role.MANAGER, hours, invoice)
    print(f"After Create Invoice  → {_fmt(hours, invoice)}")
    assert hours == HoursState.INVOICED and invoice == InvoiceState.OPEN

    invoice = approve_invoice(Role.CLIENT, invoice)
    print(f"After Approve Invoice → {_fmt(hours, invoice)}")
    assert invoice == InvoiceState.APPROVED

    print("\nHappy path completed successfully. All contracts held.\n")


def scenario_edit_after_submit() -> None:
    """Error – Consultant tries to edit hours after submission"""
    print("=== Scenario: Error – Consultant tries to edit hours after submission ===\n")

    hours = register_hours(Role.CONSULTANT, HoursState.NONE)
    hours = submit_hours(Role.CONSULTANT, hours)
    print(f"Given Hours are Submitted → {_fmt(hours, InvoiceState.NONE)}")

    try:
        edit_hours(Role.CONSULTANT, hours)
        raise AssertionError("Expected ContractViolation, but edit succeeded")
    except ContractViolation as e:
        print(f"Edit rejected as expected.")
        print(f'Contract broken: "{e.contract}"')
        assert hours == HoursState.SUBMITTED
        assert e.contract == C_EDIT_DRAFT_ONLY

    print("\nError scenario completed successfully.\n")


def scenario_consultant_creates_invoice() -> None:
    """Error – Consultant tries to create an invoice"""
    print("=== Scenario: Error – Consultant tries to create an invoice ===\n")

    hours = register_hours(Role.CONSULTANT, HoursState.NONE)
    hours = submit_hours(Role.CONSULTANT, hours)
    invoice = InvoiceState.NONE
    print(f"Given Hours are Submitted → {_fmt(hours, invoice)}")

    try:
        create_invoice(Role.CONSULTANT, hours, invoice)
        raise AssertionError("Expected ContractViolation, but create succeeded")
    except ContractViolation as e:
        print(f"Invoice creation rejected as expected.")
        print(f'Contract broken: "{e.contract}"')
        assert hours == HoursState.SUBMITTED
        assert invoice == InvoiceState.NONE
        assert e.contract == C_MANAGER_CREATES_INVOICE

    print("\nError scenario completed successfully.\n")


def main(argv: list[str]) -> int:
    which = argv[1] if len(argv) > 1 else "all"

    runners = {
        "happy": scenario_happy_path,
        "error-edit": scenario_edit_after_submit,
        "error-invoice": scenario_consultant_creates_invoice,
    }

    if which == "all":
        for name, run in runners.items():
            run()
        print("All scenarios passed.")
        return 0

    if which not in runners:
        print(
            f"Usage: {argv[0]} [all|happy|error-edit|error-invoice]",
            file=sys.stderr,
        )
        return 2

    runners[which]()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
