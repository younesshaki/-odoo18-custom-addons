from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

class WebsiteSaleInherit(WebsiteSale):

    @http.route(['/shop/cart/'], type='http', auth="public", website=True, methods=['POST'])
    def cart_update(self, product_id=None, add_qty=1, set_qty=0, **kw):
        # Perform the default operation
        res = super().cart_update(product_id=product_id, add_qty=add_qty, set_qty=set_qty, **kw)

        line_width = 2.0
        line_height = 3.0

        # Force test logic
        if product_id:
            order = request.website.sale_get_order(force_create=1)
            product_id_int = int(product_id)
            lines = order.order_line.filtered(lambda l: l.product_id.id == product_id_int)
            if lines:
                line = lines[-1]

                # Set our test values for width/length
                if line_width:
                    line.line_width = float(line_width)
                if line_height:
                    line.line_length = float(line_height)

                # Force set a known price_unit to ensure non-zero totals for testing
                # This will help verify the computations are actually running.
                line.price_unit = 20.0  # Arbitrary non-zero price to test
                
                # Force recompute area and amounts if needed
                line._compute_area()
                line._compute_amount()
                order._amount_all()  # Recompute order totals

        # Redirect back to cart to see the updated totals
        return request.redirect('/shop/cart')
