# Example: Loan application entry and credit decision

> **Intentional bad model.** Several Contracts are deliberately untestable.  
> Use this as a **larger counter-example** and as a **fixture for testing the prompts**  
> (especially `validate-tundra` and `extract-tundra`’s refusal of vague Contracts).  
> Do **not** copy its Contract style into real models.

## Why it exists

The model has a realistic shape (Roles, Relationships, States, Processes, Scenarios) but includes vague rules such as:

- “high relative to the Applicant’s income”
- “low relative to the Applicant’s income”
- applications that “fall between” automatic approval and decline

A good validator should flag those. A good extract prompt should ask for measurable thresholds instead of accepting them.

## Files

| File | Description |
|------|-------------|
| `loan-application-entry.tundra` | Deliberately flawed Tundra model (see note above) |

## What still looks “normal”

- Swedish BankID / UC domain framing
- Relationships (`Applicant of Application`, `Reviewer of Application`)
- Branching happy path, auto-decline, and Loan Officer review

Those structural parts are fine; the **Contract testability** is the intentional defect.

## See also

- Language definition: [`../../tundra.md`](../../tundra.md)
- Catalog: [`../README.md`](../README.md)
- Prompts: [`../../prompts/validate-tundra.md`](../../prompts/validate-tundra.md), [`../../prompts/extract-tundra.md`](../../prompts/extract-tundra.md)
