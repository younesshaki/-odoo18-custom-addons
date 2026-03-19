from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    customer_type = fields.Selection(string='Sales Group',selection=[('browser', 'Browser'),('consumer', 'Customer'),('vendor', 'Vendor')], default="browser")
    lead_source = fields.Many2one('cidmo.udc.values', string='Lead Source', domain="[('field_name', '=', 'lead_source')]")
    map_reference = fields.Many2one('cidmo.udc.values', string='Map Reference', domain="[('field_name', '=', 'map_reference')]")
    preferences = fields.Text(string="Preferences")

    # @api.onchange('customer_type')
    # def onchange_customer_type(self):
    #     for rec in self:
    #         if rec.customer_type:
    #             pricelist = self.env['product.pricelist'].search([('customer_type', '=', rec.customer_type)])
    #             if pricelist:
    #

        
#
# class ProductPricelist(models.Model):
#     _inherit = 'product.pricelist'
#
#     customer_type = fields.Selection(string='Sales Group',selection=[('consumer', 'Consumer'),('vendor', 'Vendor')])
#
#
#
#
#


class ResCompany(models.Model):
    _inherit = 'res.company'

    treas_location_id = fields.Many2one('stock.location', 'Remnant Location')
