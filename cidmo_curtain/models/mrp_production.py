import math

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    width = fields.Float(related="sale_line_id.width", string="Width", store=True, readonly=True)
    height = fields.Float(related="sale_line_id.height", string="Height", store=True, readonly=True)
    sale_priority = fields.Selection(
        related="sale_line_id.order_id.priority",
        string="Sale Order Priority",
        store=True,
        readonly=True,
    )
    roll_width = fields.Float(string="Roll Width", compute="_compute_roll_width", store=True)
    fitting_method = fields.Many2one(
        "cidmo.udc.values",
        string="Fitting Method",
        domain="[('field_name', '=', 'fitting_method')]",
    )
    control_side = fields.Many2one(
        "cidmo.udc.values",
        string="Control Side",
        domain="[('field_name', '=', 'control_side')]",
    )
    roll_direction = fields.Many2one(
        "cidmo.udc.values",
        string="Roll Direction",
        domain="[('field_name', '=', 'roll_direction')]",
    )
    check_measure = fields.Many2one(
        "cidmo.udc.values",
        related="sale_line_id.order_id.check_measure",
        string="Check Measure",
        store=True,
        readonly=True,
    )
    remove_product = fields.Many2one(
        "cidmo.udc.values",
        related="sale_line_id.order_id.remove_product",
        string="Remove Product",
        store=True,
        readonly=True,
    )
    split_shipping = fields.Many2one(
        "cidmo.udc.values",
        related="sale_line_id.order_id.split_shipping",
        string="Split Shipping",
        store=True,
        readonly=True,
    )
    location = fields.Selection(
        [
            ("living_room", "Living Room"),
            ("lounge", "Lounge"),
            ("bedroom_1", "Bedroom 1"),
            ("bedroom_2", "Bedroom 2"),
            ("bedroom_3", "Bedroom 3"),
            ("terrasse", "Terrasse"),
            ("balcony", "Balcony"),
            ("kitchen", "Kitchen"),
            ("bathroom", "Bathroom"),
            ("other", "Other"),
        ],
        string="Location",
        default="living_room",
    )
    location_other_1 = fields.Selection(
        [
            ("basement", "Basement"),
            ("ground_floor", "Ground Floor"),
            ("first_floor", "First Floor"),
            ("second_floor", "Second Floor"),
            ("third_floor", "Third Floor"),
            ("other", "Other"),
        ],
        string="Location Other (1)",
        default="ground_floor",
    )
    location_other_2 = fields.Selection(
        [
            ("apartment", "Apartment"),
            ("loft", "Loft"),
            ("house", "House"),
            ("bank", "Bank"),
            ("coffee_shop", "Coffee Shop"),
            ("hotel", "Hotel"),
            ("other", "Other"),
        ],
        string="Location Other (2)",
        default="house",
    )
    treas_id = fields.Many2one("stock.treas", string="Remnant")

    @api.depends("move_raw_ids", "move_raw_ids.lot_id")
    def _compute_roll_width(self):
        for production in self:
            fabric = production.move_raw_ids.filtered(lambda move: move.lot_id)
            production.roll_width = fabric[:1].width if fabric else 0

    def action_print_layout_report(self):
        return self.env.ref("cidmo_curtain.report_mrp_layout").report_action(self)

    def action_assign_treas(self):
        self.ensure_one()
        line = self.move_raw_ids.filtered(lambda move: move.lot_id)[:1]
        if not line:
            raise ValidationError("There is no products have LOT")

        return {
            "name": "Remnants",
            "view_mode": "form",
            "res_model": "stock.treas",
            "target": "new",
            "type": "ir.actions.act_window",
            "context": {
                "default_product_id": line.product_id.id,
                "default_product_uom_id": line.product_uom.id,
                "default_location_id": line.location_id.id,
                "default_location_dest_id": line.company_id.treas_location_id.id,
                "default_lot_id": line.lot_id.id,
                "default_production_id": self.id,
            },
        }

    def action_view_treas(self):
        action = self.env.ref("cidmo_curtain.action_stock_treas").read()[0]
        action["domain"] = [("production_id", "=", self.id)]
        return action

    def button_mark_done(self):
        res = super().button_mark_done()
        for production in self.filtered("treas_id"):
            production.treas_id.action_validate()
        return res


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    @api.model_create_multi
    def create(self, values_list):
        records = super().create(values_list)
        records._update_cidmo_sales_prices()
        return records

    def write(self, values):
        res = super().write(values)
        self._update_cidmo_sales_prices()
        return res

    def _update_cidmo_sales_prices(self):
        for bom in self:
            computed_price = bom.cidmo_get_price()
            if bom.product_tmpl_id:
                bom.product_tmpl_id.list_price = computed_price
                bom.product_tmpl_id.product_variant_ids.write({"list_price": computed_price})
            elif bom.product_id:
                bom.product_id.list_price = computed_price

    def cidmo_get_price(self):
        price = 0
        for bom_line in self.bom_line_ids:
            line_price = bom_line.product_id.standard_price * bom_line.product_qty
            extra = bom_line.product_id.novelty + bom_line.product_id.waste
            if extra > 0:
                line_price *= extra
            price += line_price
        price = math.ceil(price / 1)
        return math.ceil(price / 10) * 10
