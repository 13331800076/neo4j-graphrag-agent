# API Reference

## Cross-Module APIs

- `convertPurchaseToInventory` - Converts a purchase order to inventory stock. Used by Procurement and Inventory modules.
- `notifyApprovalComplete` - Sends notification when approval is complete. Used by Approval Workflow module.
- `attachDocumentToOrder` - Attaches a document to a purchase order. Used by Procurement and Attachment Management modules.

## Permissions

- PURCHASE_CREATE - Create purchase orders.
- PURCHASE_APPROVE - Approve purchase orders.
- INVENTORY_QUERY - Query inventory.
- INVENTORY_UPDATE - Update inventory.
- ATTACHMENT_UPLOAD - Upload attachments.
- ATTACHMENT_DELETE - Delete attachments.
- APPROVAL_SUBMIT - Submit approval requests.
- APPROVAL_MANAGER - Manager approval authority.
- APPROVAL_FINANCE - Finance review authority.
