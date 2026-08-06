/*
 * Happy-path implementation of the Consultant hours Tundra model.
 *
 * Generated from: consultant-hours-invoice.tundra
 * Language: ANSI C (C89/C90 compatible, no external libraries)
 */

#include <stdio.h>
#include <stdlib.h>

/* ------------------------------------------------------------------ */
/* States                                                             */
/* ------------------------------------------------------------------ */

typedef enum {
    HOURS_IN_DRAFT,
    HOURS_SUBMITTED,
    INVOICE_OPEN,
    INVOICE_APPROVED,
    INVOICE_DISPUTED
} State;

static const char *state_name(State s)
{
    switch (s) {
        case HOURS_IN_DRAFT:     return "HOURS_IN_DRAFT";
        case HOURS_SUBMITTED:    return "HOURS_SUBMITTED";
        case INVOICE_OPEN:       return "INVOICE_OPEN";
        case INVOICE_APPROVED:   return "INVOICE_APPROVED";
        case INVOICE_DISPUTED:   return "INVOICE_DISPUTED";
        default:                 return "UNKNOWN";
    }
}

/* ------------------------------------------------------------------ */
/* Contract violation                                                 */
/* ------------------------------------------------------------------ */

static void contract_violation(const char *message)
{
    fprintf(stderr, "Contract violation: %s\n", message);
    exit(1);
}

/* ------------------------------------------------------------------ */
/* Processes                                                          */
/* ------------------------------------------------------------------ */

static State register_hours(void)
{
    /* Consultant registers hours → Hours are in Draft */
    return HOURS_IN_DRAFT;
}

static State submit_hours(State current)
{
    /* Consultant submits the hours → Hours are Submitted */
    if (current != HOURS_IN_DRAFT) {
        contract_violation(
            "Hours may be edited by the Consultant only while they are in Draft"
        );
    }
    return HOURS_SUBMITTED;
}

static State create_invoice(State current)
{
    /* Manager creates an invoice from the submitted hours → Invoice is Open */
    if (current != HOURS_SUBMITTED) {
        contract_violation(
            "An invoice may be created only from Submitted hours that have not already been invoiced"
        );
    }
    return INVOICE_OPEN;
}

static State approve_invoice(State current)
{
    /* Client approves the invoice → Invoice is Approved */
    if (current != INVOICE_OPEN) {
        contract_violation(
            "Only the Client may Approve or Dispute an open invoice"
        );
    }
    return INVOICE_APPROVED;
}

/* ------------------------------------------------------------------ */
/* Scenario: Happy path – hours submitted and invoice approved        */
/* ------------------------------------------------------------------ */

static void happy_path_scenario(void)
{
    State state;

    printf("Starting Happy path scenario...\n\n");

    /* Given no hours exist
       When the Consultant registers hours */
    state = register_hours();
    printf("After Register Hours  → %s\n", state_name(state));
    if (state != HOURS_IN_DRAFT) {
        contract_violation("Expected HOURS_IN_DRAFT");
    }

    /* When the Consultant submits the hours */
    state = submit_hours(state);
    printf("After Submit Hours    → %s\n", state_name(state));
    if (state != HOURS_SUBMITTED) {
        contract_violation("Expected HOURS_SUBMITTED");
    }

    /* When the Manager creates an invoice from the submitted hours */
    state = create_invoice(state);
    printf("After Create Invoice  → %s\n", state_name(state));
    if (state != INVOICE_OPEN) {
        contract_violation("Expected INVOICE_OPEN");
    }

    /* When the Client approves the invoice */
    state = approve_invoice(state);
    printf("After Approve Invoice → %s\n", state_name(state));
    if (state != INVOICE_APPROVED) {
        contract_violation("Expected INVOICE_APPROVED");
    }

    printf("\nHappy path scenario completed successfully.\n");
    printf("All contracts held.\n");
}

int main(void)
{
    happy_path_scenario();
    return 0;
}
