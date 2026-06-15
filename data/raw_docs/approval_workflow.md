# Approval Workflow Module

The approval workflow module manages business process approvals.

## APIs

- `submitApproval` - Submits an item for approval.
- `approveRequest` - Approves a pending request.
- `rejectRequest` - Rejects a pending request.

## Workflow

1. Submit Request
2. Review Request
3. Manager Approval
4. Finance Review
5. Final Approval

## Roles

- Requester - Requires APPROVAL_SUBMIT permission.
- Manager - Requires APPROVAL_MANAGER permission.
- Finance Reviewer - Requires APPROVAL_FINANCE permission.
