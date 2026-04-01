# Odoo 19 Migration Notes

This repository now targets Odoo 19 module versions and uses `cidmo_curtain`
as the canonical curtain business module.

## Consolidation

- `cidmo_curtain` owns the curtain-specific sales, website, product, MRP, and remnant flows.
- `curtain_sales` is retained only as a compatibility shim so existing databases can upgrade
  without losing the legacy module reference.

## Core flows frozen for regression testing

- Website curtain ordering with width/height validation and cart propagation
- Sale order pricing, taxes, and invoice quantities driven by dimensions
- Manufacturing order creation from confirmed sales
- BOM scaling for width/height-driven components
- Remnant assignment, creation, and validation
- Production print flows and delivery tracking

## Upgrade work still expected in deployment

- Rebase the vendored OCA `product_configurator*` addons on their latest Odoo 19 upstream.
- Run database upgrade scripts before validating production data.
- Execute the new regression tests on an Odoo 19 environment before cutover.
