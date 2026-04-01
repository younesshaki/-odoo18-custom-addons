import math

from odoo import api, fields, models


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    c_type = fields.Selection(
        string="Type",
        selection=[("n", "None"), ("w", "Width"), ("h", "Height")],
        default="n",
    )


class ProductProduct(models.Model):
    _inherit = "product.product"

    def cidmo_get_price(self):
        bom = self.sudo().env["mrp.bom"].search(
            ["|", ("product_id", "=", self.id), ("product_tmpl_id", "=", self.product_tmpl_id.id)],
            limit=1,
        )
        if not bom:
            return False

        price = 0
        for bom_line in bom.bom_line_ids:
            line_price = bom_line.product_id.standard_price * bom_line.product_qty
            extra = bom_line.product_id.novelty + bom_line.product_id.waste
            if extra > 0:
                line_price *= extra
            price += line_price * 2

        price = math.ceil(price / 1)
        return math.ceil(price / 10) * 10

    def get_treasure_width_height(self, width, height, lot_id=False):
        new_width = width - 0.03
        new_height = height + 0.2
        quant_model = self.sudo().env["stock.quant"]
        lot_model = self.sudo().env["stock.lot"]

        if self.orientation == "w":
            if lot_id:
                lot_width = lot_id.width - 0.06
                return lot_width - new_width, new_height, lot_id

            quantities = {}
            for quant in quant_model.search(
                [
                    ("product_id", "=", self.product_variant_id.id),
                    ("inventory_quantity_auto_apply", ">", 0),
                    ("lot_id", "!=", False),
                ]
            ):
                current_lot = quant.lot_id
                lot_width = current_lot.width - 0.06
                treas_width = lot_width - new_width
                treas_height = new_height
                if treas_width * treas_height > 0:
                    quantities[current_lot.id] = {
                        "width": treas_width,
                        "height": treas_height,
                        "size": treas_width * treas_height,
                    }
            if not quantities:
                return False, False, False
            smallest_lot = min(quantities, key=lambda key: quantities[key]["size"])
            return new_width, new_height, lot_model.browse(smallest_lot)

        if self.orientation == "wh":
            if lot_id:
                lot_width = lot_id.width - 0.06
                quantities = {}
                w_treas_width = lot_width - new_width
                w_treas_height = new_height
                if w_treas_width * w_treas_height > 0:
                    quantities["w"] = {
                        "width": w_treas_width,
                        "height": w_treas_height,
                        "size": w_treas_width * w_treas_height,
                    }
                h_treas_width = lot_width - new_height
                h_treas_height = new_width
                if h_treas_width * h_treas_height > 0:
                    quantities["h"] = {
                        "width": h_treas_width,
                        "height": h_treas_height,
                        "size": h_treas_width * h_treas_height,
                    }
                if not quantities:
                    return False, False, False
                smallest_lot = min(quantities, key=lambda key: quantities[key]["size"])
                return quantities[smallest_lot]["width"], quantities[smallest_lot]["height"], lot_id

            quantities = {}
            for quant in quant_model.search(
                [
                    ("product_id", "=", self.product_variant_id.id),
                    ("inventory_quantity_auto_apply", ">", 0),
                    ("lot_id", "!=", False),
                ]
            ):
                current_lot = quant.lot_id
                lot_width = current_lot.width - 0.06
                w_treas_width = lot_width - new_width
                w_treas_height = new_height
                if w_treas_width * w_treas_height > 0:
                    quantities[f"{current_lot.id}-w"] = {
                        "new_width": new_width,
                        "new_height": new_height,
                        "width": w_treas_width,
                        "height": w_treas_height,
                        "size": w_treas_width * w_treas_height,
                    }
                h_treas_width = lot_width - new_height
                h_treas_height = new_width
                if h_treas_width * h_treas_height > 0:
                    quantities[f"{current_lot.id}-h"] = {
                        "new_width": new_height,
                        "new_height": new_width,
                        "width": h_treas_width,
                        "height": h_treas_height,
                        "size": h_treas_width * h_treas_height,
                    }
            if not quantities:
                return False, False, False
            smallest_lot = min(quantities, key=lambda key: quantities[key]["size"])
            return (
                quantities[smallest_lot]["new_width"],
                quantities[smallest_lot]["new_height"],
                lot_model.browse(int(smallest_lot.split("-")[0])),
            )
        return False, False, False


class ProductTemplate(models.Model):
    _inherit = "product.template"

    TYPE_MULTIPLICATOR_SELECTION = [
        ("normal", "Ordinary Product"),
        ("novelty", "Novelty 100%"),
        ("waste", "Waste 50%"),
        ("alum", "Aluminium 25%"),
    ]

    day_night = fields.Boolean(string="Day & night")
    novelty = fields.Float(string="Novelty")
    waste = fields.Float(string="Waste")
    sold_width = fields.Boolean(string="Sold by Width (m)", default=False)
    sold_length = fields.Boolean(string="Sold by Length (m)", default=False)
    type_multiplicator = fields.Selection(
        selection=TYPE_MULTIPLICATOR_SELECTION,
        string="Type",
        default="normal",
    )
    muliplicator = fields.Float(string="Multiplicator", default=1.0)
    flooring = fields.Boolean(string="Is Mounting Bracket", default=False)
    orientation = fields.Selection(
        string="Orientation",
        selection=[("w", "Width-wise"), ("wh", "Width-wise & Height-wise")],
    )
    calculate_format = fields.Selection(
        string="Calculation Qty Format",
        selection=[("m", "M"), ("m2", "M2")],
        default="m",
    )
    is_formul_1 = fields.Boolean(string="Is a Mounting Bracket")

    c_widths = fields.Char(string="Width")
    c_openess_factor = fields.Integer(string="Openess Factor")
    c_color_fastness = fields.Integer(string="Color Fastness")
    c_maximum_load = fields.Float(string="Maximum Load")
    c_certifications = fields.Char(string="Certifications")
    c_weights = fields.Char(string="Weight")
    c_hs_code = fields.Integer(string="HS Code")
    c_composition = fields.Char(string="Composition")
    c_origin = fields.Selection(string="Origin", selection=[("china", "China"), ("turkey", "Turkey")])

    thickness = fields.Char(string="Thickness")
    openness_factor = fields.Char(string="Openness Factor")
    color_fastness = fields.Char(string="Color Fastness")
    certifications = fields.Char(string="Certifications")
    sheer_band = fields.Char(string="Sheer Band")
    solid_band = fields.Char(string="Solid Band")
    uom = fields.Char(string="UoM")
    origin = fields.Char(string="Origin")
    weight = fields.Char(string="Weight")
    hs_code = fields.Char(string="HS Code")
    composition = fields.Char(string="Composition")

    @api.onchange("sold_width", "sold_length", "flooring")
    def _onchange_sold_width_length(self):
        unit_uom = self.env.ref("uom.product_uom_unit")
        meter_uom = self.env.ref("uom.product_uom_meter")
        sqm_uom = self.env.ref("uom.uom_square_meter")

        for product in self:
            if product.flooring:
                if product.sold_width and product.sold_length:
                    product.sold_width = False
                    product.sold_length = False
                uom = meter_uom
            elif product.sold_width and product.sold_length:
                uom = sqm_uom
            elif product.sold_width or product.sold_length:
                uom = meter_uom
            else:
                uom = unit_uom
            product.uom_id = uom
            product.uom_po_id = uom

    @api.onchange("type_multiplicator", "standard_price")
    def _onchange_type_multiplicator(self):
        for product in self:
            multiplier = {
                "normal": 1.0,
                "novelty": 1.0,
                "waste": 0.5,
                "alum": 0.25,
            }.get(product.type_multiplicator or "normal", 1.0)
            product.muliplicator = multiplier

    def cidmo_get_price(self):
        bom = self.sudo().env["mrp.bom"].search([("product_tmpl_id", "=", self.id)], limit=1)
        if not bom:
            return False

        price = 0
        for bom_line in bom.bom_line_ids:
            line_price = bom_line.product_id.standard_price * bom_line.product_qty
            extra = bom_line.product_id.novelty + bom_line.product_id.waste
            if extra > 0:
                line_price *= extra
            price += line_price * 2

        price = math.ceil(price / 1)
        return math.ceil(price / 10) * 10
