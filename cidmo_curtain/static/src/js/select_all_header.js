/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
import { useService } from "@web/core/utils/hooks";

patch(ListRenderer.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
    },

    async onCidmoSelectAll(ev) {
        const checked = ev.target.checked;
        const root = this.props.list?.model?.root;
        if (!root?.resId) return;
        const method = checked ? 'action_select_all' : 'action_deselect_all';
        await this.orm.call('production.dailly.details', method, [root.resId]);
        await root.load();
        root.model.notify();
    },
});
