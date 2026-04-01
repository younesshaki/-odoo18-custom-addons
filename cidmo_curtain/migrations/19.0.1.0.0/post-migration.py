from odoo import SUPERUSER_ID, api


LEGACY_ORDER_VALUE_MAP = {
    "check_measure": {
        "required": "Required",
        "not_required": "Not Required",
    },
    "remove_product": {
        "removal": "Removal & Disposal",
        "not_removal": "Not Removal",
        "no_removal": "No Removal",
    },
    "split_shipping": {
        "permitted": "Permitted",
        "not_permitted": "Not Permitted",
    },
}


def _ensure_udc_value(env, field_name, label):
    udc_model = env["cidmo.udc.values"].sudo()
    value = udc_model.search([("field_name", "=", field_name), ("name", "=", label)], limit=1)
    if not value:
        value = udc_model.create({"field_name": field_name, "name": label})
    return value


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    cr.execute(
        """
        UPDATE ir_model_fields
           SET module = 'cidmo_curtain'
         WHERE module = 'curtain_sales'
           AND model IN ('sale.order', 'sale.order.line', 'mrp.production', 'product.template', 'product.product')
        """
    )

    order_model = env["sale.order"].sudo().with_context(active_test=False)
    for field_name, mapping in LEGACY_ORDER_VALUE_MAP.items():
        legacy_column = f"x_legacy_{field_name}"
        cr.execute(
            """
            SELECT 1
              FROM information_schema.columns
             WHERE table_name = 'sale_order'
               AND column_name = %s
            """,
            (legacy_column,),
        )
        if not cr.fetchone():
            continue
        for legacy_value, label in mapping.items():
            udc_value = _ensure_udc_value(env, field_name, label)
            records = order_model.search([(legacy_column, "=", legacy_value)])
            if records:
                records.write({field_name: udc_value.id})
