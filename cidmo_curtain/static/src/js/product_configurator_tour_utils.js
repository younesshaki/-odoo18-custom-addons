/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { SaleOrderLineProductField } from '@sale/js/sale_product_field';
import { ProductConfiguratorDialog } from "@sale/js/product_configurator_dialog/product_configurator_dialog";
import { serializeDateTime } from "@web/core/l10n/dates";
import { applyProduct } from '@sale/js/sale_product_field';


patch(SaleOrderLineProductField.prototype, {

    async _openProductConfigurator(edit=false) {
        const saleOrderRecord = this.props.record.model.root;
        const saleOrderLine = this.props.record.data;
        let ptavIds = this._getVariantPtavIds(saleOrderLine);
        let customPtavs = [];

        console.log("Opening product configurator for sale order line", saleOrderLine);
        if (edit) {
            /**
             * no_variant and custom attribute don't need to be given to the configurator for new
             * products.
             */
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
}
)





patch(ProductConfiguratorDialog.prototype, {

    _getAdditionalRpcParams() {
        // Override this method to provide additional RPC parameters if needed.
        console.log(this.props);
        return {
            height: this.props.Height,
            width: this.props.Width,
        };
    }
}
)


