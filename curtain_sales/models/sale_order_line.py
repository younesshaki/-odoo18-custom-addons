from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_width = fields.Float(string='Width (m)' , store=True)
    line_length = fields.Float(string='Height (m)', store=True)
    line_depth = fields.Float(string='Depth (m)', store=True)
    line_area = fields.Float(string='size (m2)', compute='_compute_area', store=True)
    line_volume = fields.Float(string='volume (m3)', compute='_compute_area', store=True)

    @api.depends('line_width', 'line_length', 'line_depth', 'width', 'height', 'dimension_z')
    def _compute_area(self):
        for line in self:
            width = line.line_width or line.width
            length = line.line_length or line.height
            depth = line.line_depth or line.dimension_z

            if width and length:
                area = width * length
            else:
                area = 0.0

            line.line_area = area

            if depth and area > 0:
                line.line_volume = area * depth
            else:
                line.line_volume = area


    @api.depends('product_uom_qty', 'line_area', 'line_volume', 'price_unit', 'discount', 'tax_id', 'width', 'height', 'dimension_z')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            # first priority: explicit line_volume (line_depth) -> 3D
            # second: line_area -> 2D
            # third: old width/height/dimension_z from cidmo_curtain fields
            if line.line_volume > 0:
                qty = line.product_uom_qty * line.line_volume
            elif line.line_area > 0:
                qty = line.product_uom_qty * line.line_area
            elif line.width > 0 and line.height > 0:
                depth = line.dimension_z > 0 and line.dimension_z or 1.0
                qty = line.product_uom_qty * line.width * line.height * depth
            else:
                qty = line.product_uom_qty

            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res['quantity'] = self.product_uom_qty * (self.line_volume if self.line_depth > 0 else self.line_area)
        if self.line_width and self.line_length:
            dims = f"Width: {self.line_width:.2f}, Length: {self.line_length:.2f}"
            if self.line_depth > 0:
                dims += f", Depth: {self.line_depth:.2f}"
            res['name'] += f"\n({dims})"
        return res
    

    # @api.onchange('product_id', 'line_width', 'line_length')
    # def _onchange_dimension_description(self):
    #     for line in self:
    #         if line.product_id:
    #             name = line.product_id.get_product_multiline_description_sale()
    #             if line.line_width and line.line_length:
    #                 name += f"\n(Width: {line.line_width:.2f}, Length: {line.line_length:.2f})"
    #             line.name = name

    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     """Map product attribute values to order line fields."""
    #     if self.product_id:
    #         # Reset length and width fields
    #         self.line_length = 0.0
    #         self.line_width = 0.0

    #         # Fetch product attribute values
    #         attribute_values = self.product_id.product_template_attribute_value_ids
    #         for attr_value in attribute_values:
    #             if attr_value.attribute_id.name == "Length":
    #                 # Convert attribute value to float
    #                 try:
    #                     self.line_length = float(attr_value.name)
    #                 except ValueError:
    #                     self.line_length = 0.0
    #             elif attr_value.attribute_id.name == "Width":
    #                 # Convert attribute value to float
    #                 try:
    #                     self.line_width = float(attr_value.name)
    #                 except ValueError:
    #                     self.line_width = 0.0

    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     """Map product attribute values to order line fields and show alerts."""
    #     if self.product_id:
    #         messages = []
    #         for attr_value in self.product_id.product_template_attribute_value_ids:
    #             if attr_value.attribute_id.name == "Length":
    #                 try:
    #                     self.line_length = float(attr_value.name)
    #                     messages.append(f"Length Found: {self.line_length}")
    #                 except ValueError:
    #                     messages.append(f"Length Found: {attr_value.name} (Invalid Number)")
    #                     self.line_length = 0.0
    #             elif attr_value.attribute_id.name == "Width":
    #                 try:
    #                     self.line_width = float(attr_value.name)
    #                     messages.append(f"Width Found: {self.line_width}")
    #                 except ValueError:
    #                     messages.append(f"Width Found: {attr_value.name} (Invalid Number)")
    #                     self.line_width = 0.0
            
    #         if messages:
    #             return {
    #                 'warning': {
    #                     'title': "Product Attribute Alert",
    #                     'message': "\n".join(messages),
    #                 }
    #             }

    @api.model
    def create(self, vals):
        # Create the line first
        line = super(SaleOrderLine, self).create(vals)
        line._update_dimensions_from_custom_attributes()
        return line
    def write(self, vals):
        # If the context has 'dimension_update' set, don't run the update again
        if not self.env.context.get('dimension_update'):
            # Call the method with a context to avoid re-entry
            self.with_context(dimension_update=True)._update_dimensions_from_custom_attributes()

        return super(SaleOrderLine, self).write(vals)

    def _update_dimensions_from_custom_attributes(self):
        for line in self:
            length_val = line.line_length
            width_val = line.line_width

            if line.product_custom_attribute_value_ids:
                for custom_value in line.product_custom_attribute_value_ids:
                    attribute_name = custom_value.custom_product_template_attribute_value_id.attribute_id.name
                    attribute_value = custom_value.custom_value or ''
                    if attribute_name == "Length":
                        length_val = float(attribute_value) if attribute_value.replace('.', '', 1).isdigit() else 0.0
                    elif attribute_name == "Width":
                        width_val = float(attribute_value) if attribute_value.replace('.', '', 1).isdigit() else 0.0

            # Now update fields with write(), but since we are in 'dimension_update' context, 
            # this will not call _update_dimensions_from_custom_attributes() again.
            line.with_context(dimension_update=True).write({
                'line_length': length_val,
                'line_width': width_val,
            })

    @api.onchange('product_id', 'product_custom_attribute_value_ids')
    def _onchange_product_id(self):
        """Capture product configurator values for custom attributes."""
        if self.product_id and self.product_custom_attribute_value_ids:
            messages = []
            for custom_value in self.product_custom_attribute_value_ids:
                attribute_name = custom_value.custom_product_template_attribute_value_id.attribute_id.name
                attribute_value = custom_value.custom_value

                if attribute_name == "Length":
                    self.line_length = float(attribute_value) if attribute_value.replace('.', '', 1).isdigit() else 0.0
                    messages.append(f"Length Entered: {self.line_length}")
                elif attribute_name == "Width":
                    self.line_width = float(attribute_value) if attribute_value.replace('.', '', 1).isdigit() else 0.0
                    messages.append(f"Width Entered: {self.line_width}")

            if messages:
                return {
                    'warning': {
                        'title': "Product Attribute Alert",
                        'message': "\n".join(messages),
                    }
                }
