from odoo import fields, models, api


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    default_location_treas_id = fields.Many2one('stock.location', 'Source Location',
        help="This is the default Remnant location for this operation type. ")




class StockMove(models.Model):
    _inherit = 'stock.move'


    treas_id = fields.Many2one('stock.treas', 'Remnant')
    source_treas_id = fields.Many2one('stock.treas', 'Remnant')
    width = fields.Float('Width')
    lot_id = fields.Many2one('stock.lot', 'Lot/Serial Number')
    lot_width = fields.Float('Width')
    treas_source = fields.Boolean('Remnant Source', compute='_compute_treas_source', store=True)




    @api.depends('location_id', 'company_id')
    def _compute_treas_source(self):
        for rec in self:
            rec.treas_source = rec.location_id == rec.company_id.treas_location_id

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id:
            self.lot_width = self.lot_id.width


    @api.onchange('treas_id')
    def _onchange_treas_id(self):
        if self.treas_id:
            self.location_id = self.treas_id.location_dest_id
            self.lot_id = self.treas_id.lot_id

    @api.onchange('location_id')
    def _onchange_location_id_cidmo(self):
        if self.location_id and self.treas_id:
            self.treas_id = False
            self.lot_id = False



class StockTreas(models.Model):
    _name = 'stock.treas'
    _description = 'Remnants'

    name = fields.Char("Name", compute="_compute_name")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    origin = fields.Char(string='Source Document')
    product_id = fields.Many2one('product.product', 'Product')
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    move_ids = fields.One2many('stock.move', 'source_treas_id')
    lot_id = fields.Many2one('stock.lot', 'Lot/Serial Number')
    location_id = fields.Many2one('stock.location', 'Source Location')
    location_dest_id = fields.Many2one(related="company_id.treas_location_id", string='Destination Location')
    production_id = fields.Many2one('mrp.production', 'Production Order')
    qty = fields.Float('Height')
    width = fields.Float('Width')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')],
        string='Status', default="draft", readonly=True)
    date_done = fields.Datetime('Date', readonly=True)
    is_used = fields.Boolean('Is Used', default=False)


    def _compute_name(self):
        for rec in self:
            rec.name = "W." + str(rec.width) + ' * H.' + str(rec.qty)

    @api.model
    def create(self, values):
        res = super(StockTreas, self).create(values)
        if self._context.get("default_production_id") and res.production_id:
            res.production_id.write({'treas_id': res.id})
        return res

    def get_product_treas(self, product_id, width, height):
        available_treas = self.search([('is_used', '!=', True)])
        for size in available_treas.mapped('move_ids').filtered(lambda x: x.product_id.id == product_id.id):
            new_width = width
            new_height = height + 0.2
            if product_id.orientation == 'w':
                if size.width >= new_width and size.product_uom_qty >= new_height:
                    return size.treas_id.id
            elif product_id.orientation == 'wh':
                if size.width >= new_width and size.product_uom_qty >= new_height:
                    return size.treas_id.id
                elif size.width >= new_height and size.product_uom_qty >= new_width:
                    return size.treas_id.id




        return False


    def action_validate(self):
        self.ensure_one()
        self.write({'state': 'done', 'date_done': fields.Datetime.now()})
        self._create_stock_moves()
        return True

    def _create_stock_moves(self):
        self.ensure_one()
        move = self.env['stock.move'].create({
            'product_id': self.product_id.id,
            'product_uom_qty': self.qty,
            'width': self.width,
            'product_uom': self.product_uom_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'source_treas_id': self.id,
            'company_id': self.company_id.id,
        })
        move._action_confirm()
        move._action_assign()
        move._action_done()
        return move

class StockLot(models.Model):
    _inherit = 'stock.lot'

    width = fields.Float('Width')


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    image = fields.Image(max_width=1024, max_height=1024)
