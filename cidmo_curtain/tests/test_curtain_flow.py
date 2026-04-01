from odoo.tests.common import TransactionCase


class TestCurtainFlow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Curtain Test Customer"})
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.main_product = cls.env["product.product"].create(
            {
                "name": "Configured Curtain",
                "type": "consu",
            }
        )
        cls.component = cls.env["product.product"].create(
            {
                "name": "Curtain Fabric",
                "type": "consu",
                "calculate_format": "m2",
            }
        )
        cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.main_product.product_tmpl_id.id,
                "product_qty": 1,
                "type": "normal",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.component.id,
                            "product_qty": 1,
                        },
                    )
                ],
            }
        )

    def _create_order(self):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "warehouse_id": self.warehouse.id,
            }
        )

    def test_dimension_amounts_and_invoice_quantity(self):
        order = self._create_order()
        line = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.main_product.id,
                "product_uom_qty": 2,
                "price_unit": 10,
                "line_width": 2,
                "line_length": 3,
                "line_depth": 0.5,
                "product_uom_id": self.main_product.uom_id.id,
                "name": self.main_product.name,
            }
        )

        self.assertEqual(line.width, 2.0)
        self.assertEqual(line.height, 3.0)
        self.assertEqual(line.dimension_z, 0.5)
        self.assertEqual(line.line_area, 6.0)
        self.assertEqual(line.line_volume, 3.0)
        self.assertEqual(line.size, 3.0)
        self.assertEqual(line.price_subtotal, 60.0)

        invoice_vals = line._prepare_invoice_line()
        self.assertEqual(invoice_vals["quantity"], 6.0)
        self.assertIn("Width: 2.00", invoice_vals["name"])

    def test_action_create_mo_so_uses_dimension_quantity(self):
        order = self._create_order()
        line = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.main_product.id,
                "product_uom_qty": 1,
                "price_unit": 100,
                "line_width": 2,
                "line_length": 3,
                "product_uom_id": self.main_product.uom_id.id,
                "name": self.main_product.name,
            }
        )

        line.action_create_mo_so()
        production = self.env["mrp.production"].search([("sale_line_id", "=", line.id)], limit=1)

        self.assertTrue(production)
        component_move = production.move_raw_ids.filtered(lambda move: move.product_id == self.component)
        self.assertTrue(component_move)
        self.assertEqual(component_move.product_uom_qty, 6.0)
