import math

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _default_date_delivery(self):
        return fields.Datetime.today() + relativedelta(days=7)

    customer_type = fields.Selection(string="Sales Group", related="partner_id.customer_type")
    priority = fields.Selection(
        string="Priority",
        selection=[("standard", "Standard"), ("express", "Express")],
        default="standard",
        required=True,
    )
    priority_type = fields.Selection(
        [("normal", "Normal"), ("special", "Special")],
        string="Priority Type",
        default="normal",
    )
    lead_source = fields.Selection(
        [
            ("drive_past", "Drive Past"),
            ("previous_customer", "Previous Customer"),
            ("printing", "Printing"),
            ("own_lead", "Own Lead"),
            ("recommended", "Recommended"),
            ("internet", "Internet"),
            ("other", "Other"),
        ],
        string="Lead Source",
    )
    commitment_date = fields.Datetime(string="Delivery Date", default=_default_date_delivery)

    check_measure = fields.Many2one(
        "cidmo.udc.values",
        string="Check Measure",
        domain="[('field_name', '=', 'check_measure')]",
    )
    remove_product = fields.Many2one(
        "cidmo.udc.values",
        string="Remove Product",
        domain="[('field_name', '=', 'remove_product')]",
    )
    split_shipping = fields.Many2one(
        "cidmo.udc.values",
        string="Split Shipping",
        domain="[('field_name', '=', 'split_shipping')]",
    )

    @api.onchange("priority")
    def onchange_priority(self):
        base_date = self.date_order or fields.Datetime.now()
        if self.priority == "express":
            self.commitment_date = base_date.replace(hour=22, minute=0)
        else:
            self.commitment_date = base_date + relativedelta(days=7)

    def action_add_priority(self):
        self.ensure_one()
        qty = sum(
            self.order_line.filtered(lambda line: not line.is_delivery and not line.is_express).mapped(
                "product_uom_qty"
            )
        )
        return {
            "name": _("Add a priority method"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "cidmo.wizard.priority",
            "target": "new",
            "context": {
                "active_model": "sale.order",
                "active_ids": self.ids,
                "default_quantity": qty,
            },
        }

    def action_add_installation(self):
        self.ensure_one()
        qty = sum(
            self.order_line.filtered(
                lambda line: not line.is_delivery and not line.is_express and not line.is_install
            ).mapped("product_uom_qty")
        )
        product = self.env.ref("cidmo_curtain.cidmo_product_install_paid")
        price_unit = product.product_variant_ids[0].list_price

        return {
            "name": _("Add an Installation method"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "cidmo.wizard.install",
            "target": "new",
            "context": {
                "active_model": "sale.order",
                "active_ids": self.ids,
                "default_quantity": qty,
                "default_price_unit": price_unit,
            },
        }

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            order.order_line.filtered(lambda line: line.product_id and not line.is_delivery).action_create_mo_so()
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    width = fields.Float(string="Width")
    height = fields.Float(string="Height")
    dimension_z = fields.Float(string="Dimension Z")
    line_width = fields.Float(string="Width (m)", store=True)
    line_length = fields.Float(string="Height (m)", store=True)
    line_depth = fields.Float(string="Depth (m)", store=True)
    size = fields.Float(string="Size", compute="_compute_size")
    line_area = fields.Float(string="Size (m2)", compute="_compute_area", store=True)
    line_volume = fields.Float(string="Volume (m3)", compute="_compute_area", store=True)
    is_express = fields.Boolean("Is Express")
    is_install = fields.Boolean("Is Installation")

    @staticmethod
    def _safe_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _normalize_dimension_values(self, values):
        values = dict(values)
        if self._context.get("width") and "width" not in values and "line_width" not in values:
            values["width"] = self._context["width"]
        if self._context.get("height") and "height" not in values and "line_length" not in values:
            values["height"] = self._context["height"]

        pairs = (
            ("line_width", "width"),
            ("line_length", "height"),
            ("line_depth", "dimension_z"),
        )
        for modern_field, legacy_field in pairs:
            if modern_field in values:
                normalized = self._safe_float(values[modern_field])
                values[modern_field] = normalized
                values[legacy_field] = normalized
            elif legacy_field in values:
                normalized = self._safe_float(values[legacy_field])
                values[legacy_field] = normalized
                values[modern_field] = normalized
        return values

    def _get_dimension_triplet(self):
        self.ensure_one()
        width = self.line_width or self.width
        height = self.line_length or self.height
        depth = self.line_depth or self.dimension_z
        return width, height, depth

    @api.depends("line_width", "line_length", "line_depth", "width", "height", "dimension_z")
    def _compute_area(self):
        for line in self:
            width, height, depth = line._get_dimension_triplet()
            area = width * height if width and height else 0.0
            line.line_area = area
            line.line_volume = area * depth if depth and area > 0 else area

    @api.depends("line_width", "line_length", "line_depth", "width", "height", "dimension_z")
    def _compute_size(self):
        for line in self:
            width, height, depth = line._get_dimension_triplet()
            line.size = width * height * depth if depth and width and height else width * height

    @api.depends(
        "product_uom_qty",
        "line_area",
        "line_volume",
        "price_unit",
        "discount",
        "tax_ids",
        "width",
        "height",
        "dimension_z",
    )
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            width, height, depth = line._get_dimension_triplet()
            if line.line_volume > 0:
                qty = line.product_uom_qty * line.line_volume
            elif line.line_area > 0:
                qty = line.product_uom_qty * line.line_area
            elif width > 0 and height > 0:
                qty = line.product_uom_qty * width * height * (depth or 1.0)
            else:
                qty = line.product_uom_qty

            taxes = line.tax_ids.compute_all(
                price,
                line.order_id.currency_id,
                qty,
                product=line.product_id,
                partner=line.order_id.partner_shipping_id,
            )
            line.update(
                {
                    "price_tax": taxes["total_included"] - taxes["total_excluded"],
                    "price_total": taxes["total_included"],
                    "price_subtotal": taxes["total_excluded"],
                }
            )

    @api.onchange(
        "width",
        "height",
        "dimension_z",
        "line_width",
        "line_length",
        "line_depth",
        "product_uom_qty",
        "price_unit",
        "discount",
        "tax_ids",
    )
    def _onchange_dimensions(self):
        for line in self:
            width, height, depth = line._get_dimension_triplet()
            line.width = width
            line.height = height
            line.dimension_z = depth
            line.line_width = width
            line.line_length = height
            line.line_depth = depth
            line._compute_area()
            line._compute_size()
            line._compute_amount()

    def _prepare_dimension_updates_from_custom_attributes(self):
        self.ensure_one()
        updates = {}
        for custom_value in self.product_custom_attribute_value_ids:
            attribute_name = (
                custom_value.custom_product_template_attribute_value_id.attribute_id.name or ""
            ).strip().lower()
            attribute_value = custom_value.custom_value or ""
            if attribute_name == "width":
                updates["line_width"] = self._safe_float(attribute_value)
            elif attribute_name in {"height", "length"}:
                updates["line_length"] = self._safe_float(attribute_value)
            elif attribute_name == "depth":
                updates["line_depth"] = self._safe_float(attribute_value)
        return updates

    @api.model_create_multi
    def create(self, vals_list):
        normalized_vals_list = [self._normalize_dimension_values(values) for values in vals_list]
        lines = super().create(normalized_vals_list)
        if not self.env.context.get("dimension_update"):
            for line in lines:
                updates = line._prepare_dimension_updates_from_custom_attributes()
                if updates:
                    line.with_context(dimension_update=True).write(
                        line._normalize_dimension_values(updates)
                    )
        return lines

    def write(self, values):
        res = super().write(self._normalize_dimension_values(values))
        if not self.env.context.get("dimension_update"):
            for line in self:
                updates = line._prepare_dimension_updates_from_custom_attributes()
                if updates:
                    line.with_context(dimension_update=True).write(line._normalize_dimension_values(updates))
        return res

    @api.onchange("product_id", "product_custom_attribute_value_ids")
    def _onchange_product_id(self):
        if self.product_id and self.product_custom_attribute_value_ids:
            updates = self._prepare_dimension_updates_from_custom_attributes()
            normalized = self._normalize_dimension_values(updates)
            self.update(normalized)
            messages = []
            if normalized.get("line_width"):
                messages.append(f"Width Entered: {normalized['line_width']}")
            if normalized.get("line_length"):
                messages.append(f"Length Entered: {normalized['line_length']}")
            if normalized.get("line_depth"):
                messages.append(f"Depth Entered: {normalized['line_depth']}")
            if messages:
                return {
                    "warning": {
                        "title": "Product Attribute Alert",
                        "message": "\n".join(messages),
                    }
                }
        return {}

    def _prepare_base_line_for_taxes_computation(self, **kwargs):
        self.ensure_one()
        width, height, depth = self._get_dimension_triplet()
        qty = self.product_uom_qty
        if self.line_volume > 0:
            qty = self.product_uom_qty * self.line_volume
        elif self.line_area > 0:
            qty = self.product_uom_qty * self.line_area
        elif width > 0 and height > 0:
            qty = self.product_uom_qty * width * height
            if depth > 0:
                qty *= depth

        return self.env["account.tax"]._prepare_base_line_for_taxes_computation(
            self,
            **{
                "tax_ids": self.tax_ids,
                "quantity": qty,
                "partner_id": self.order_id.partner_id,
                "currency_id": self.order_id.currency_id or self.order_id.company_id.currency_id,
                "rate": self.order_id.currency_rate,
                **kwargs,
            },
        )

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        width, height, depth = self._get_dimension_triplet()
        if self.line_volume > 0:
            qty = self.product_uom_qty * self.line_volume
        elif self.line_area > 0:
            qty = self.product_uom_qty * self.line_area
        elif width > 0 and height > 0:
            qty = self.product_uom_qty * width * height * (depth or 1.0)
        else:
            qty = self.product_uom_qty

        res["quantity"] = qty
        if width and height:
            dims = f"Width: {width:.2f}, Length: {height:.2f}"
            if depth > 0:
                dims += f", Depth: {depth:.2f}"
            res["name"] += f"\n({dims})"
        return res

    def action_create_mo_so(self):
        production_model = self.env["mrp.production"]
        production_location = self.env["stock.location"].search(
            [("usage", "=", "production"), ("company_id", "=", self.env.company.id)],
            limit=1,
        )
        for line in self:
            existing_count = production_model.search_count([("sale_line_id", "=", line.id)])
            quantity_to_create = max(int(line.product_uom_qty) - existing_count, 0)
            if not quantity_to_create:
                continue

            width, height, _depth = line._get_dimension_triplet()
            order = line.order_id
            stock_picking_type = self.env["stock.picking.type"].search(
                [
                    ("warehouse_id", "=", order.warehouse_id.id),
                    ("code", "=", "mrp_operation"),
                    ("company_id", "in", [False, order.company_id.id]),
                ],
                limit=1,
            )
            bom = self.env["mrp.bom"].sudo().search(
                [
                    "|",
                    ("product_id", "=", line.product_id.id),
                    ("product_tmpl_id", "=", line.product_id.product_tmpl_id.id),
                ],
                limit=1,
            )
            if not (bom and stock_picking_type):
                continue

            for offset in range(quantity_to_create):
                index = existing_count + offset + 1
                production_name = order.name.replace("S", "WH/MO/")
                if int(line.product_uom_qty) > 1:
                    production_name += f".{index}"

                move_raw_ids = []
                for bom_line in bom.bom_line_ids:
                    component_product = bom_line.product_id
                    if component_product.is_formul_1 and width:
                        qty = math.floor(((width - 0.3) / 0.95) + 2)
                    elif component_product.calculate_format == "m2" and width and height:
                        qty = width * height * bom_line.product_qty
                    elif component_product.calculate_format == "m" and width:
                        qty = width * bom_line.product_qty
                    else:
                        qty = bom_line.product_qty

                    move_vals = {
                        "product_id": component_product.id,
                        "product_uom": component_product.uom_id.id,
                        "product_uom_qty": qty,
                        "price_unit": line.get_price_unit_mo(bom_line),
                        "location_id": order.warehouse_id.lot_stock_id.id,
                        "location_dest_id": production_location.id,
                    }
                    if component_product.orientation and width and height:
                        treas_id = self.env["stock.treas"].get_product_treas(component_product, width, height)
                        if treas_id:
                            move_vals["treas_id"] = treas_id
                            move_vals["location_id"] = self.env.company.treas_location_id.id
                            move_vals["width"] = width
                        else:
                            width_t, _height_t, lot_id = component_product.get_treasure_width_height(
                                width,
                                height,
                                False,
                            )
                            if lot_id:
                                move_vals["lot_id"] = lot_id.id
                                move_vals["width"] = width_t
                                move_vals["lot_width"] = lot_id.width
                    move_raw_ids.append((0, 0, move_vals))

                production_model.create(
                    {
                        "name": production_name,
                        "product_id": line.product_id.id,
                        "product_qty": 1,
                        "product_uom_id": line.product_id.uom_id.id,
                        "picking_type_id": stock_picking_type.id,
                        "location_src_id": stock_picking_type.default_location_src_id.id,
                        "location_dest_id": stock_picking_type.default_location_dest_id.id,
                        "bom_id": bom.id,
                        "date_deadline": order.date_order,
                        "date_start": order.date_order,
                        "sale_line_id": line.id,
                        "move_raw_ids": move_raw_ids,
                    }
                )

    def get_price_unit_mo(self, bom_line):
        return bom_line.product_id.standard_price * bom_line.product_qty


class cidmo_udc_values(models.Model):
    _name = "cidmo.udc.values"
    _description = "Cidmo Udc Values"

    name = fields.Char("Name")
    field_name = fields.Char(string="Field")
