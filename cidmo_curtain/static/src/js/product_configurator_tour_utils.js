/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { SaleOrderLineProductField } from '@sale/js/sale_product_field';
import { ProductConfiguratorDialog } from "@sale/js/product_configurator_dialog/product_configurator_dialog";
import { Product } from "@sale/js/product/product";
import { serializeDateTime } from "@web/core/l10n/dates";
import { x2ManyCommands } from "@web/core/orm_service";
import { getSelectedCustomPtav } from "@sale/js/sale_utils";

// applyProduct is not exported from sale_product_field in Odoo 18, so we define it locally.
async function applyProduct(record, product) {
    const customAttributesCommands = [x2ManyCommands.set([])];
    for (const ptal of product.attribute_lines) {
        const selectedCustomPTAV = getSelectedCustomPtav(ptal);
        if (selectedCustomPTAV) {
            customAttributesCommands.push(
                x2ManyCommands.create(undefined, {
                    custom_product_template_attribute_value_id: [selectedCustomPTAV.id, "we don't care"],
                    custom_value: ptal.customValue,
                })
            );
        }
    }
    const noVariantPTAVIds = product.attribute_lines
        .filter(ptal => ptal.create_variant === "no_variant")
        .flatMap(ptal => ptal.selected_attribute_value_ids);

    await record._update({
        product_id: [product.id, product.display_name],
        product_uom_qty: product.quantity,
        product_no_variant_attribute_value_ids: [x2ManyCommands.set(noVariantPTAVIds)],
        product_custom_attribute_value_ids: customAttributesCommands,
    });
}


patch(SaleOrderLineProductField.prototype, {

    async _openProductConfigurator(edit=false) {
        const saleOrderRecord = this.props.record.model.root;
        const saleOrderLine = this.props.record.data;
        let ptavIds = this._getVariantPtavIds(saleOrderLine);
        let customPtavs = [];

        console.log("Opening product configurator for sale order line", saleOrderLine);
        if (edit) {
            ptavIds.push(...this._getNoVariantPtavIds(saleOrderLine));
            customPtavs = await this._getCustomPtavs(saleOrderLine);
        }

        this.dialog.add(ProductConfiguratorDialog, {
            productTemplateId: saleOrderLine.product_template_id[0],
            ptavIds: ptavIds,
            customPtavs: customPtavs,
            quantity: saleOrderLine.product_uom_qty,
            productUOMId: saleOrderLine.product_uom[0],
            companyId: saleOrderRecord.data.company_id[0],
            pricelistId: saleOrderRecord.data.pricelist_id[0],
            Height: saleOrderLine.height,
            Width: saleOrderLine.width,
            currencyId: saleOrderLine.currency_id[0],
            soDate: serializeDateTime(saleOrderRecord.data.date_order),
            edit: edit,
            save: async (mainProduct, optionalProducts) => {
                await Promise.all([
                    applyProduct(this.props.record, mainProduct),
                    ...optionalProducts.map(async product => {
                        const line = await saleOrderRecord.data.order_line.addNewRecord({
                            position: 'bottom', mode: 'readonly'
                        });
                        await applyProduct(line, product);
                    }),
                ]);
                this._onProductUpdate();
                saleOrderRecord.data.order_line.leaveEditMode();
            },
            discard: () => {
                saleOrderRecord.data.order_line.delete(this.props.record);
            },
            ...this._getAdditionalDialogProps(),
        });
    }
});


// Declare Height and Width as valid optional props on ProductConfiguratorDialog
ProductConfiguratorDialog.props = {
    ...ProductConfiguratorDialog.props,
    Height: { type: [Number, Boolean], optional: true },
    Width: { type: [Number, Boolean], optional: true },
};

// Declare height and width as valid optional props on Product (passed via t-props from ProductList)
Product.props = {
    ...Product.props,
    height: { type: [Number, Boolean], optional: true },
    width: { type: [Number, Boolean], optional: true },
};

patch(ProductConfiguratorDialog.prototype, {
    _getAdditionalRpcParams() {
        console.log(this.props);
        return {
            height: this.props.Height,
            width: this.props.Width,
        };
    }
});
