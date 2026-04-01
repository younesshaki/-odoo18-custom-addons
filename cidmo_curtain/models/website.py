from odoo import models


class Website(models.Model):
    _inherit = "website"

    def _cart_update(self, product_id, add_qty=1, set_qty=0, attributes=None, **kwargs):
        """Keep configurable dimension fields in sync with the sale order line."""
        res = super()._cart_update(
            product_id,
            add_qty=add_qty,
            set_qty=set_qty,
            attributes=attributes,
            **kwargs,
        )
        order_line = self.env["sale.order.line"].browse(res.get("line_id"))
        if not order_line:
            return res

        width = kwargs.get("width") or kwargs.get("line_width")
        height = kwargs.get("height") or kwargs.get("line_length")
        depth = kwargs.get("line_depth")

        if attributes:
            for attribute_id, value in attributes:
                ptav = self.env["product.template.attribute.value"].browse(attribute_id)
                name = (ptav.attribute_id.name or "").strip().lower()
                if name == "width":
                    width = value
                elif name in {"height", "length"}:
                    height = value
                elif name == "depth":
                    depth = value

        updates = {}
        if width not in (None, ""):
            updates["line_width"] = order_line._safe_float(width)
            updates["width"] = updates["line_width"]
        if height not in (None, ""):
            updates["line_length"] = order_line._safe_float(height)
            updates["height"] = updates["line_length"]
        if depth not in (None, ""):
            updates["line_depth"] = order_line._safe_float(depth)
            updates["dimension_z"] = updates["line_depth"]

        if updates:
            order_line.with_context(dimension_update=True).write(updates)
            order_line._compute_area()
            order_line._compute_size()
            order_line._compute_amount()
        return res
