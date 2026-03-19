from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'


    TYPE_MULTIPLICATOR_SELECTION = [
        ('normal' , 'Is Ordonary product'),
        ('novelty', 'Is Novelty 100%'),
        ('waste', 'Is Waste 50%'),
        ('alum', 'Is Aluminium 25%'),
    ]

    sold_width = fields.Boolean(string="Sold by Width (m)", default=False)
    sold_length = fields.Boolean(string="Sold by Length (m)", default=False)
    type_multiplicator = fields.Selection(
        selection=TYPE_MULTIPLICATOR_SELECTION,
        string="Type", default='normal'
    )
    muliplicator = fields.Float(string="Multiplicator", default=1.0)
    flooring = fields.Boolean(string="Is Mounting bracket", default=False)

    # Technical fields
    thickness = fields.Char(string="Thickness")
    openness_factor = fields.Char(string="Openness Factor")
    color_fastness = fields.Char(string="Color Fastness")
    certifications = fields.Char(string="Certifications")
    sheer_band = fields.Char(string="Sheer Band")
    solid_band = fields.Char(string="Solid Band")

    # Logistics fields
    uom = fields.Char(string="UoM")
    origin = fields.Char(string="Origin")
    weight = fields.Char(string="Weight")
    hs_code = fields.Char(string="HS Code")
    composition = fields.Char(string="Composition")

    list_price = fields.Float(
        string='Sales Price',
        compute='_compute_list_price',
        store=True,
    )
    


    @api.onchange('sold_width', 'sold_length', 'flooring')
    def _onchange_sold_width_length(self):
        # Fetch UoM references only once
        unit_uom = self.env.ref('uom.product_uom_unit')
        meter_uom = self.env.ref('uom.product_uom_meter')
        sqm_uom = self.env.ref('uom.uom_square_meter')

        for product in self:
            width, length, floor = product.sold_width, product.sold_length, product.flooring

            if floor:
                # If flooring is True
                if width and length:
                    # Reset dimensions and use meter
                    product.sold_width = False
                    product.sold_length = False
                    uom = meter_uom
                else:
                    # Flooring without both dimensions: use unit
                    uom = meter_uom
            else:
                # If flooring is False
                if width and length:
                    # Both width and length are set: use square meter
                    uom = sqm_uom
                elif width or length:
                    # Only one dimension is set: use meter
                    uom = meter_uom
                else:
                    # No dimensions, no flooring: use unit
                    uom = unit_uom

            product.uom_id = uom
            product.uom_po_id = uom



    @api.onchange('is_alum')
    def _onchange_is_alum(self):
        if self.is_alum:
            self.is_waste = True
        else:
            self.is_waste = False


    @api.onchange('type_multiplicator', 'standard_price')
    def _onchange_type_multiplicator(self):
        if self.type_multiplicator:
            base_price = self.standard_price or 0.0
            if self.type_multiplicator == 'novelty':
                self.list_price = base_price * 1.0  # 100%
            elif self.type_multiplicator == 'waste':
                self.list_price = base_price * 0.5  # 50%
            elif self.type_multiplicator == 'alum':
                self.list_price = base_price * 0.25  # 25%
            else:
                self.list_price = base_price
            # Update lst_price on variants
            for variant in self.product_variant_ids:
                variant.lst_price = self.list_price




class ProductProduct(models.Model):
    _inherit = 'product.product'

    lst_price = fields.Float(
        string='Sales Price',
        compute='_compute_lst_price',
        store=True,
    )

    @api.depends('product_tmpl_id.list_price')
    def _compute_lst_price(self):
        for variant in self:
            variant.lst_price = variant.product_tmpl_id.list_price
