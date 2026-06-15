# Inventory Module

The inventory module manages stock levels and warehouse operations.

## APIs

- `queryInventory` - Queries current inventory levels.
- `updateStock` - Updates stock quantity.
- `transferStock` - Transfers stock between warehouses.

## Roles

- Warehouse Clerk - Requires INVENTORY_QUERY permission.
- Warehouse Manager - Requires INVENTORY_UPDATE permission.

## Workflow

1. Stock Inquiry
2. Check Availability
3. Update Stock
4. Confirm Receipt

## Business Objects

- InventoryItem
- Warehouse
- StockTransfer
