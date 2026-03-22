/** @odoo-module */

import { registry } from "@web/core/registry";

/**
 * Download a URL as a file using a hidden <a download> click.
 * Unlike window.open(), this is NOT subject to popup blockers.
 */
function downloadUrl(url) {
    const a = document.createElement('a');
    a.href = url;
    a.download = '';          // tells the browser to download, not navigate
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

async function cidmoMultiPrint(env, action) {
    const urls = (action.params && action.params.report_urls) || [];
    if (!urls.length) return;

    for (let i = 0; i < urls.length; i++) {
        if (i > 0) {
            // Small delay so the browser has time to start the first download
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        downloadUrl(urls[i]);
    }
}

registry.category("actions").add("cidmo_multi_print", cidmoMultiPrint);
