from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import http
from odoo.http import request


class WebsiteSaleCustom(WebsiteSale):

    @http.route()
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        res = super(WebsiteSaleCustom, self).cart_update(product_id, add_qty=add_qty, set_qty=set_qty, **kw)
        
        order = request.website.sale_get_order()
        if order:
            # Extract attribute values from kw or request
            line_length_val = kw.get('line_length')  # or parse from product_custom_attribute_value_ids
            line_width_val = kw.get('line_width')

            # Find the line just created or updated
            line = order.order_line.filtered(lambda l: l.product_id.id == product_id and l.product_custom_attribute_value_ids == ...)
            if line:
                line.write({
                    'line_length': float(line_length_val) if line_length_val else 0.0,
                    'line_width': float(line_width_val) if line_width_val else 0.0,
                })

        return res
