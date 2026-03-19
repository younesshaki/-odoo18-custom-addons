from odoo import models, fields, api , _
from odoo.exceptions import UserError
from collections import defaultdict
import math

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    priority_type = fields.Selection([('normal', 'Normal'),('special', 'Special')], string='Priority', default='normal')

    lead_source = fields.Selection([
        ('drive_past', 'Drive Past'),
        ('previous_customer', 'Previous Customer'),
        ('printing', 'Printing'),
        ('own_lead', 'Own Lead'),
        ('recommended', 'Recommended'),
        ('internet', 'Internet'),
        ('other', 'Other')
    ], string='Lead Source')
    split_shipping = fields.Selection(
        selection=[
            ("not_permitted", "Not Permitted"),
            ("permitted", "Permitted"),
        ],
        string="Split Shipping",
    )

    check_measure = fields.Selection(
        selection=[
            ("not_required", "Not Required"),
            ("required", "Required"),
        ],
        string="Check Measure",
    )

    remove_product = fields.Selection(
        selection=[
            ("not_removal", "Not Removal"),
            ("removal", "Removal & Disposal"),
        ],
        string="Remove Product",
    )

    @api.depends('order_line.price_total')
    def _compute_tax_totals(self):
        for order in self:
            amount_untaxed = sum(order.order_line.mapped('price_subtotal'))
            amount_total = sum(order.order_line.mapped('price_total'))
            amount_tax = amount_total - amount_untaxed

            tax_totals = {
                'amount_untaxed': amount_untaxed,
                'amount_total': amount_total,
                'formatted_amount_total': order.currency_id.format(amount_total),
                'subtotals': [{
                    'name': 'Untaxed Amount',
                    'amount': amount_untaxed,
                    'formatted_amount': order.currency_id.format(amount_untaxed),
                }],
                'groups_by_subtotal': {
                    'Untaxed Amount': [{
                        'group_key': 'tax_group_1',
                        'tax_group_name': 'Tax',
                        'tax_group_amount': amount_tax,
                        'tax_group_base_amount': amount_untaxed,
                        'formatted_tax_group_amount': order.currency_id.format(amount_tax),
                        'formatted_tax_group_base_amount': order.currency_id.format(amount_untaxed),
                    }]
                },
                'subtotals_order': ['Untaxed Amount'],
                'groups_by_subtotal_order': {'Untaxed Amount': ['tax_group_1']},
                'display_tax_base': False, #default value
            }
            order.tax_totals = tax_totals

    def _amount_by_group(self):
        for order in self:
            amount_untaxed = sum(order.order_line.mapped('price_subtotal'))
            amount_total = sum(order.order_line.mapped('price_total'))
            amount_tax = amount_total - amount_untaxed
            
            order.amount_by_group = [(
                'Tax', amount_tax, amount_untaxed,
                order.currency_id.format(amount_tax), order.currency_id.format(amount_untaxed),
                1,
            )]

    def action_create_mrp_orders(self):
        MrpProduction = self.env['mrp.production']
        created_mrp_orders = MrpProduction
        for order in self:
            for line in order.order_line:
                # Check if an MRP order already exists for this sale order line
                existing_mrp_orders = MrpProduction.search([('origin', '=', order.name), ('product_id', '=', line.product_id.id)])
                if existing_mrp_orders:
                    continue  # Skip creating a new MRP order if one already exists
                if line.product_id.type == 'product' and line.product_id.bom_ids:
                    # Call _bom_find with the correct arguments
                    bom_dict = self.env['mrp.bom']._bom_find(products=line.product_id, company_id=order.company_id.id)

                    # Retrieve the bom for the current product
                    bom = bom_dict.get(line.product_id)

                    if bom:
                        # Create the manufacturing order
                        mo_vals = {
                            'product_id': line.product_id.id,
                            'product_qty': line.product_uom_qty,
                            'product_uom_id': line.product_uom.id,
                            'width': line.line_width,
                            'height': line.line_length,
                            'bom_id': bom.id,
                            'origin': order.name,
                        }
                        mo = MrpProduction.create(mo_vals)

                        # Adjust quantities for specific products in move_raw_ids
                        for move in mo.move_raw_ids:
                            #if product unit of measure is square meter
                            if move.product_id.uom_id == self.env.ref('uom.product_uom_square_meter'):
                                move.product_uom_qty = line.line_area * mo.product_qty
                            #if product unit of measure is meter
                            elif move.product_id.uom_id == self.env.ref('uom.product_uom_meter'):
                                move.product_uom_qty = line.line_width * mo.product_qty
                            #if product is flooring
                            move.product_uom_qty = math.ceil(line.line_width / 0.7) * mo.product_qty
                            # move.product_uom_qty *= move.product_id.muliplicator

                        mo.action_confirm()
                        created_mrp_orders |= mo
                    else:
                        raise UserError(_("No valid Bill of Materials found for the product: %s") % line.product_id.name)
        if not created_mrp_orders:
            raise UserError(_("No manufacturing orders were created."))

        if len(created_mrp_orders) == 1:
            return {
                'name': _('Manufacturing Order'),
                'view_mode': 'form',
                'res_model': 'mrp.production',
                'res_id': created_mrp_orders.id,
                'type': 'ir.actions.act_window',
            }
        else:
            return {
                'name': _('Created Manufacturing Orders'),
                'view_mode': 'tree,form',
                'res_model': 'mrp.production',
                'domain': [('id', 'in', created_mrp_orders.ids)],
                'type': 'ir.actions.act_window',
            }

    def action_confirm(self):
        # Confirm the sale order as usual
        res = super(SaleOrder, self).action_confirm()

        # Automatically create MRP orders
        for order in self:
            mrp_orders = self._create_mrp_orders(order)
            if mrp_orders:
                order.message_post(body=_("MRP Orders have been created for this sale order."))

        return res

    def _create_mrp_orders(self, order):
        """
        Create MRP orders for the products in the confirmed sale order
        that have a Bill of Materials (BoM) and adjust quantities as needed.
        """
        mrp_order_obj = self.env['mrp.production']
        mrp_orders = []

        for line in order.order_line:
            product = line.product_id
            if product.type == 'product' and product.bom_ids:
                #create a manufacturing order for each product unite in the sale order line
                for i in range(int(line.product_uom_qty)):
                    # Check if the product is manufactured and has a BoM
                    bom = product.bom_ids[0]  # Assume the first BoM
                    values = {
                        'product_id': product.id,
                        'product_uom_id': product.uom_id.id,
                        'product_qty': 1,
                        'bom_id': bom.id,
                        'origin': order.name,
                        'sale_order_line_id': line.id,  
                        'width': line.line_width,      
                        'height': line.line_length,    
                    }
                    mo = mrp_order_obj.create(values)
                    mrp_orders.append(mo)

                    # Adjust quantities for specific products in move_raw_ids
                    for move in mo.move_raw_ids:
                        #if product unit of measure is square meter 
                        if move.product_id.uom_id == self.env.ref('uom.uom_square_meter'):
                            move.product_uom_qty = line.line_area  * 2
                        #if product unit of measure is meter
                        elif move.product_id.uom_id == self.env.ref('uom.product_uom_meter'):
                            move.product_uom_qty = line.line_width 
                        #if product is flooring
                        elif move.product_id.flooring:
                            move.product_uom_qty = math.floor(((line.line_width -0.3)/0.95)+2)
                

                    # Confirm the manufacturing order
                    mo.action_confirm()

        return mrp_orders