"""
Happy-path implementation of the Consultant hours Tundra model.

Generated from: consultant-hours-invoice.tundra
Language: Python (standard library only)
"""

from enum import Enum, auto


class State(Enum):
    HOURS_IN_DRAFT = auto()
    HOURS_SUBMITTED = auto()
    INVOICE_OPEN = auto()
    INVOICE_APPROVED = auto()
    INVOICE_DISPUTED = auto()


class ContractViolation(Exception):
    pass


# ------------------------------------------------------------------
# Processes
# ------------------------------------------------------------------

def register_hours() -> State:
    """Consultant registers hours → Hours are in Draft"""
    return State.HOURS_IN_DRAFT


def submit_hours(current: State) -> State:
    """Consultant submits the hours → Hours are Submitted"""
    if current != State.HOURS_IN_DRAFT:
        raise ContractViolation(
            "Hours may be edited by the Consultant only while they are in Draft"
        )
    return State.HOURS_SUBMITTED


def create_invoice(current: State) -> State:
    """Manager creates an invoice from the submitted hours → Invoice is Open"""
    if current != State.HOURS_SUBMITTED:
        raise ContractViolation(
            "An invoice may be created only from Submitted hours that have not already been invoiced"
        )
    return State.INVOICE_OPEN


def approve_invoice(current: State) -> State:
    """Client approves the invoice → Invoice is Approved"""
    if current != State.INVOICE_OPEN:
        raise ContractViolation(
            "Only the Client may Approve or Dispute an open invoice"
        )
    return State.INVOICE_APPROVED


# ------------------------------------------------------------------
# Scenario: Happy path – hours submitted and invoice approved
# ------------------------------------------------------------------

def happy_path_scenario() -> None:
    print("Starting Happy path scenario...\n")

    # Given no hours exist
    # When the Consultant registers hours
    state = register_hours()
    print(f"After Register Hours  → {state.name}")
    assert state == State.HOURS_IN_DRAFT

    # When the Consultant submits the hours
    state = submit_hours(state)
    print(f"After Submit Hours    → {state.name}")
    assert state == State.HOURS_SUBMITTED

    # When the Manager creates an invoice from the submitted hours
    state = create_invoice(state)
    print(f"After Create Invoice  → {state.name}")
    assert state == State.INVOICE_OPEN

    # When the Client approves the invoice
    state = approve_invoice(state)
    print(f"After Approve Invoice → {state.name}")
    assert state == State.INVOICE_APPROVED

    print("\nHappy path scenario completed successfully.")
    print("All contracts held.")


if __name__ == "__main__":
    happy_path_scenario()
