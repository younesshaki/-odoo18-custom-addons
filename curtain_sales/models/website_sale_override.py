from odoo import models
import logging

_logger = logging.getLogger(__name__)

class Website(models.Model):
    _inherit = 'website'

    def _cart_update(self, product_id, add_qty=1, set_qty=0, attributes=None, **kwargs):
        """Override cart update to calculate qty * width * length."""
        res = super(Website, self)._cart_update(product_id, add_qty, set_qty, attributes, **kwargs)

        # Get the sale order line created or updated
        order_line = self.env['sale.order.line'].browse(res.get('line_id'))
        if not order_line:
            return res

        if attributes:
            for attribute_id, value in attributes:
                attribute = self.env['product.template.attribute.value'].browse(attribute_id)
                if attribute.attribute_id.name == "Width":
                    order_line.line_width = float(value) if value.replace('.', '', 1).isdigit() else 1.0
                elif attribute.attribute_id.name == "Length":
                    order_line.line_length = float(value) if value.replace('.', '', 1).isdigit() else 1.0

            # Recompute the area and total quantity
            order_line._compute_area()
            order_line._compute_amount()

        return res
