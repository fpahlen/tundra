/*
 * Reference implementation of the Consultant hours Tundra model.
 *
 * Implements: models/consultant-hours-invoice.tundra
 * Language: ANSI C (C89/C90 compatible, no external libraries)
 *
 * Demonstrates Roles as actors, separate state per subject (Hours vs Invoice),
 * fail-fast Contracts, and both happy-path and error Scenarios.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ------------------------------------------------------------------ */
/* Roles and states (one state type per subject)                      */
/* ------------------------------------------------------------------ */

typedef enum {
    ROLE_CONSULTANT,
    ROLE_MANAGER,
    ROLE_CLIENT
} Role;

typedef enum {
    HOURS_NONE,
    HOURS_DRAFT,
    HOURS_SUBMITTED,
    HOURS_INVOICED
} HoursState;

typedef enum {
    INVOICE_NONE,
    INVOICE_OPEN,
    INVOICE_APPROVED,
    INVOICE_DISPUTED
} InvoiceState;

/* Contract texts — match the .tundra model */
static const char *C_EDIT_DRAFT_ONLY =
    "Hours may be edited by the Consultant only while they are in Draft";
static const char *C_INVOICE_FROM_SUBMITTED =
    "An invoice may be created only from Submitted hours that have not already been invoiced";
static const char *C_CLIENT_APPROVE_DISPUTE =
    "Only the Client may Approve or Dispute an open invoice";
static const char *C_MANAGER_CREATES_INVOICE =
    "Only the Manager may create an invoice";

static const char *hours_name(HoursState h)
{
    switch (h) {
        case HOURS_NONE:      return "NONE";
        case HOURS_DRAFT:     return "DRAFT";
        case HOURS_SUBMITTED: return "SUBMITTED";
        case HOURS_INVOICED:  return "INVOICED";
        default:              return "UNKNOWN";
    }
}

static const char *invoice_name(InvoiceState i)
{
    switch (i) {
        case INVOICE_NONE:     return "NONE";
        case INVOICE_OPEN:     return "OPEN";
        case INVOICE_APPROVED: return "APPROVED";
        case INVOICE_DISPUTED: return "DISPUTED";
        default:               return "UNKNOWN";
    }
}

/* Non-local jump style: return 0 on success, 1 on contract violation.
   On violation, *err_out is set to the contract text. */

static int register_hours(Role actor, HoursState hours, HoursState *out,
                          const char **err_out)
{
    if (actor != ROLE_CONSULTANT) {
        *err_out = "Hours may be registered only by the Consultant";
        return 1;
    }
    if (hours != HOURS_NONE) {
        *err_out = "Register Hours requires that no hours exist yet";
        return 1;
    }
    *out = HOURS_DRAFT;
    return 0;
}

static int edit_hours(Role actor, HoursState hours, HoursState *out,
                      const char **err_out)
{
    if (actor != ROLE_CONSULTANT || hours != HOURS_DRAFT) {
        *err_out = C_EDIT_DRAFT_ONLY;
        return 1;
    }
    *out = HOURS_DRAFT;
    return 0;
}

static int submit_hours(Role actor, HoursState hours, HoursState *out,
                        const char **err_out)
{
    if (actor != ROLE_CONSULTANT) {
        *err_out = "Submit Hours requires Actor Consultant";
        return 1;
    }
    if (hours != HOURS_DRAFT) {
        *err_out = "Submit Hours requires Hours are in Draft";
        return 1;
    }
    *out = HOURS_SUBMITTED;
    return 0;
}

static int create_invoice(Role actor, HoursState hours, InvoiceState invoice,
                          HoursState *hours_out, InvoiceState *invoice_out,
                          const char **err_out)
{
    if (actor != ROLE_MANAGER) {
        *err_out = C_MANAGER_CREATES_INVOICE;
        return 1;
    }
    if (hours != HOURS_SUBMITTED || invoice != INVOICE_NONE) {
        *err_out = C_INVOICE_FROM_SUBMITTED;
        return 1;
    }
    *hours_out = HOURS_INVOICED;
    *invoice_out = INVOICE_OPEN;
    return 0;
}

static int approve_invoice(Role actor, InvoiceState invoice,
                           InvoiceState *out, const char **err_out)
{
    if (actor != ROLE_CLIENT || invoice != INVOICE_OPEN) {
        *err_out = C_CLIENT_APPROVE_DISPUTE;
        return 1;
    }
    *out = INVOICE_APPROVED;
    return 0;
}

static void die_unexpected(const char *msg)
{
    fprintf(stderr, "Unexpected failure: %s\n", msg);
    exit(1);
}

/* ------------------------------------------------------------------ */
/* Scenarios                                                          */
/* ------------------------------------------------------------------ */

static void scenario_happy_path(void)
{
    HoursState hours = HOURS_NONE;
    InvoiceState invoice = INVOICE_NONE;
    const char *err = NULL;

    printf("=== Scenario: Happy path – hours submitted and invoice approved ===\n\n");

    if (register_hours(ROLE_CONSULTANT, hours, &hours, &err))
        die_unexpected(err);
    printf("After Register Hours  → hours=%s, invoice=%s\n",
           hours_name(hours), invoice_name(invoice));
    if (hours != HOURS_DRAFT)
        die_unexpected("Expected HOURS_DRAFT");

    if (submit_hours(ROLE_CONSULTANT, hours, &hours, &err))
        die_unexpected(err);
    printf("After Submit Hours    → hours=%s, invoice=%s\n",
           hours_name(hours), invoice_name(invoice));
    if (hours != HOURS_SUBMITTED)
        die_unexpected("Expected HOURS_SUBMITTED");

    if (create_invoice(ROLE_MANAGER, hours, invoice, &hours, &invoice, &err))
        die_unexpected(err);
    printf("After Create Invoice  → hours=%s, invoice=%s\n",
           hours_name(hours), invoice_name(invoice));
    if (hours != HOURS_INVOICED || invoice != INVOICE_OPEN)
        die_unexpected("Expected HOURS_INVOICED and INVOICE_OPEN");

    if (approve_invoice(ROLE_CLIENT, invoice, &invoice, &err))
        die_unexpected(err);
    printf("After Approve Invoice → hours=%s, invoice=%s\n",
           hours_name(hours), invoice_name(invoice));
    if (invoice != INVOICE_APPROVED)
        die_unexpected("Expected INVOICE_APPROVED");

    printf("\nHappy path completed successfully. All contracts held.\n\n");
}

static void scenario_edit_after_submit(void)
{
    HoursState hours = HOURS_NONE;
    HoursState after;
    const char *err = NULL;

    printf("=== Scenario: Error – Consultant tries to edit hours after submission ===\n\n");

    if (register_hours(ROLE_CONSULTANT, hours, &hours, &err))
        die_unexpected(err);
    if (submit_hours(ROLE_CONSULTANT, hours, &hours, &err))
        die_unexpected(err);
    printf("Given Hours are Submitted → hours=%s, invoice=NONE\n",
           hours_name(hours));

    if (!edit_hours(ROLE_CONSULTANT, hours, &after, &err)) {
        fprintf(stderr, "Expected ContractViolation, but edit succeeded\n");
        exit(1);
    }
    printf("Edit rejected as expected.\n");
    printf("Contract broken: \"%s\"\n", err);
    if (hours != HOURS_SUBMITTED)
        die_unexpected("Hours should remain SUBMITTED");
    if (strcmp(err, C_EDIT_DRAFT_ONLY) != 0)
        die_unexpected("Wrong contract text");

    printf("\nError scenario completed successfully.\n\n");
}

static void scenario_consultant_creates_invoice(void)
{
    HoursState hours = HOURS_NONE;
    InvoiceState invoice = INVOICE_NONE;
    HoursState h2;
    InvoiceState i2;
    const char *err = NULL;

    printf("=== Scenario: Error – Consultant tries to create an invoice ===\n\n");

    if (register_hours(ROLE_CONSULTANT, hours, &hours, &err))
        die_unexpected(err);
    if (submit_hours(ROLE_CONSULTANT, hours, &hours, &err))
        die_unexpected(err);
    printf("Given Hours are Submitted → hours=%s, invoice=%s\n",
           hours_name(hours), invoice_name(invoice));

    if (!create_invoice(ROLE_CONSULTANT, hours, invoice, &h2, &i2, &err)) {
        fprintf(stderr, "Expected ContractViolation, but create succeeded\n");
        exit(1);
    }
    printf("Invoice creation rejected as expected.\n");
    printf("Contract broken: \"%s\"\n", err);
    if (hours != HOURS_SUBMITTED || invoice != INVOICE_NONE)
        die_unexpected("State should be unchanged");
    if (strcmp(err, C_MANAGER_CREATES_INVOICE) != 0)
        die_unexpected("Wrong contract text");

    printf("\nError scenario completed successfully.\n\n");
}

int main(int argc, char **argv)
{
    const char *which = (argc > 1) ? argv[1] : "all";

    if (strcmp(which, "all") == 0) {
        scenario_happy_path();
        scenario_edit_after_submit();
        scenario_consultant_creates_invoice();
        printf("All scenarios passed.\n");
        return 0;
    }
    if (strcmp(which, "happy") == 0) {
        scenario_happy_path();
        return 0;
    }
    if (strcmp(which, "error-edit") == 0) {
        scenario_edit_after_submit();
        return 0;
    }
    if (strcmp(which, "error-invoice") == 0) {
        scenario_consultant_creates_invoice();
        return 0;
    }

    fprintf(stderr, "Usage: %s [all|happy|error-edit|error-invoice]\n", argv[0]);
    return 2;
}
