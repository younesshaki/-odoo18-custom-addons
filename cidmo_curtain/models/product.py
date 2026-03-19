from odoo import fields, models, api
from odoo.exceptions import ValidationError
import math

class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    c_type = fields.Selection(string='Type', selection=[('n', 'None'),('w', 'Width'),('h', 'Height')], default='n')




class ProductProduct(models.Model):
    _inherit = 'product.product'

    # def _get_no_variant_attributes_price_extra(self, combination):
    #     res = super(ProductProduct, self)._get_no_variant_attributes_price_extra(combination=combination)
    #     return res


    def cidmo_get_price(self):
        bom_check = self.sudo().env['mrp.bom'].search(['|', ('product_id', '=', self.id),
                                                ('product_tmpl_id', '=', self.product_tmpl_id.id)],
                                               limit=1)
        if bom_check:
            price = 0
            for b_line in bom_check.bom_line_ids:
                # GET COST PRICE
                product_price = b_line.product_id.standard_price
                b_price = product_price * b_line.product_qty
                extra = b_line.product_id.novelty + b_line.product_id.waste
                if extra > 0:
                    b_price = b_price * extra

                # GET SELL PRICE (Vendor = 150%, Consumer = 200%)
                # if line.order_id.customer_type == 'vendor':
                #     b_price = b_price * 1.5
                # else:
                b_price = b_price * 2
                price += b_price

            price = math.ceil(price / 1)
            price = math.ceil(price / 10) * 10
            return price
        else:
            return False



    def get_treasure_width_height(self, width, height, lot_id=False):
        new_width = width - 0.03
        new_height = height + 0.2
        if self.orientation == 'w':
            if lot_id:
                lot_width = lot_id.width - 0.06
                treas_width = lot_width - new_width
                treas_height = new_height
                return treas_width, treas_height, lot_id
            else:
                quantities = {}
                for quant in self.sudo().env['stock.quant'].search([('product_id', '=', self.product_variant_id.id),('inventory_quantity_auto_apply', '>', 0),('lot_id', '!=', False)]):
                    lot_id = quant.lot_id
                    lot_width = lot_id.width - 0.06
                    treas_width = lot_width - new_width
                    treas_height = new_height
                    if treas_width*treas_height > 0:
                        quantities[lot_id.id] = {'width': treas_width, 'height': treas_height, 'size': treas_width*treas_height}

                smallest_lot = min(quantities, key=lambda k: quantities[k]['size'])
                return new_width, new_height, self.sudo().env['stock.lot'].browse(smallest_lot)


        elif self.orientation == 'wh':
            if lot_id:
                lot_width = lot_id.width - 0.06

                quantities = {}
                w_treas_width = lot_width - new_width
                w_treas_height = new_height
                if w_treas_width * w_treas_height > 0:
                    quantities['w'] = {'width': w_treas_width, 'height': w_treas_height, 'size': w_treas_width * w_treas_height}

                h_treas_width = lot_width - new_height
                h_treas_height = new_width
                if h_treas_width * h_treas_height > 0:
                    quantities['h'] = {'width': h_treas_width, 'height': h_treas_height, 'size': h_treas_width * h_treas_height}

                smallest_lot = min(quantities, key=lambda k: quantities[k]['size'])
                return quantities[smallest_lot]['width'], quantities[smallest_lot]['height'], lot_id
            else:
                quantities = {}
                for quant in self.sudo().env['stock.quant'].search(
                        [('product_id', '=', self.product_variant_id.id), ('inventory_quantity_auto_apply', '>', 0),
                         ('lot_id', '!=', False)]):
                    lot_id = quant.lot_id
                    lot_width = lot_id.width - 0.06
                    w_treas_width = lot_width - new_width
                    w_treas_height = new_height
                    if w_treas_width * w_treas_height > 0:
                        quantities[str(lot_id.id) + '-w'] = {'new_width': new_width, 'new_height': new_height,'width': w_treas_width, 'height': w_treas_height,
                                           'size': w_treas_width * w_treas_height}

                    h_treas_width = lot_width - new_height
                    h_treas_height = new_width
                    if h_treas_width * h_treas_height > 0:
                        quantities[str(lot_id.id) + '-h'] = {'new_width': new_height, 'new_height': new_width , 'width': h_treas_width, 'height': h_treas_height,
                                           'size': h_treas_width * h_treas_height}

                smallest_lot = min(quantities, key=lambda k: quantities[k]['size'])

                return quantities[smallest_lot]['new_width'], quantities[smallest_lot]['new_height'], self.sudo().env['stock.lot'].browse(int(smallest_lot.split('-')[0]))
        else:
            return False,False,False




class ProductTemplate(models.Model):
    _inherit = 'product.template'

    day_night = fields.Boolean(string='Day & night')

    novelty = fields.Float(string='Novelty')
    waste = fields.Float(string='Waste')
    orientation = fields.Selection(
        string='Orientation',
        selection=[
            ('w', 'Width-wise'),
            ('wh', 'Width-wise & Height-wise'),
        ])
    calculate_format = fields.Selection(
        string='Calculation QTY format',
        selection=[
            ('m', 'M'),
            ('m2', 'M2'),
        ], default="m")
    is_formul_1 = fields.Boolean(string='Is a Mounting Bracket')

    # TECHNICAL
    c_widths = fields.Char(string='Width')
    c_openess_factor = fields.Integer(string='Openess Factor')
    c_color_fastness = fields.Integer(string='Color Fastness')
    c_maximum_load = fields.Float(string='Maximum Load')
    c_certifications = fields.Char(string='certifications')

    # LOGISTICS
    c_weights = fields.Char(string='Weight')
    c_hs_code = fields.Integer(string='HS Code')
    c_composition = fields.Char(string='Composition')
    c_origin = fields.Selection(string='Origin', selection=[('china', 'China'),('turkey', 'Turkey')])


    # def _get_sales_prices(self, website):
    #     records = super(ProductTemplate, self)._get_sales_prices(website)
    #     for template in records:
    #         product = self.env['product.template'].browse(template)
    #         price = product.cidmo_get_price()
    #         if price:
    #             records[template]['price_reduce'] = price
    #             records[template]['base_price'] = price
    #     return records
    #
    # def _get_additionnal_combination_info(self, product_or_template, quantity, date, website):
    #     res = super(ProductTemplate, self)._get_additionnal_combination_info(product_or_template, quantity, date, website)
    #
    #     price = product_or_template.cidmo_get_price()
    #     if price and price > 0:
    #         res['list_price'] = price
    #         res['price'] = price
    #         res['base_unit_price'] = price
    #     return res



    def cidmo_get_price(self):
        bom_check = self.sudo().env['mrp.bom'].search([('product_tmpl_id', '=', self.id)],
                                                      limit=1)
        if bom_check:
            price = 0
            for b_line in bom_check.bom_line_ids:
                # GET COST PRICE
                product_price = b_line.product_id.standard_price
                b_price = product_price * b_line.product_qty
                extra = b_line.product_id.novelty + b_line.product_id.waste
                if extra > 0:
                    b_price = b_price * extra

                # GET SELL PRICE (Vendor = 150%, Consumer = 200%)
                # if line.order_id.customer_type == 'vendor':
                #     b_price = b_price * 1.5
                # else:
                b_price = b_price * 2
                price += b_price

            price = math.ceil(price / 1)
            price = math.ceil(price / 10) * 10
            return price
        else:
            return False