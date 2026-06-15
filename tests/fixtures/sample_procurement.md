# Procurement Module

The procurement module handles purchase orders and supplier management.

## APIs

- `createPurchaseOrder` - Creates a new purchase order.
- `querySupplier` - Queries supplier information.

## Roles

- Procurement Clerk - Requires PURCHASE_CREATE permission.
- Procurement Manager - Requires PURCHASE_APPROVE permission.

## Workflow

1. Submit Request
2. Manager Approval
3. Create Order
4. Inventory Receiving
