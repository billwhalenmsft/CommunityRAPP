// =====================================================
//  Service Toolkit – Side Pane Loader
//  Web Resource: bw_ServiceToolkitLoader
//
//  Attach to Case (incident) main form → OnLoad event.
//  Creates a side pane with the wrench icon that renders
//  the "Customer Service Quick Wizard" Custom Page
//  (bw_ordermodificationwizard_9400f) directly in the
//  Xrm.App.sidePanes framework.
//
//  Prerequisites:
//    - Custom Page "bw_ordermodificationwizard_9400f"
//      must be added to the app module (no nav needed).
//    - Icon web resource: cr74e_navigation-wrench (SVG)
// =====================================================

var BW = BW || {};
BW.ServiceToolkit = BW.ServiceToolkit || {};

(function () {
    "use strict";

    var PANE_ID = "ServiceToolkit";
    var PANE_TITLE = "Service Toolkit";
    var PANE_WIDTH = 400;
    var PANE_ICON = "WebResources/cr74e_navigation-wrench";
    var PAGE_NAME = "bw_ordermodificationwizard_9400f";

    /**
     * Extract context IDs from the host form.
     * Returns an object with caseId, accountId, accountName,
     * and serialNumber so the Custom Page can reference the
     * case for timeline notes, the account for order lookups,
     * and the serial number for warranty lookup auto-fill.
     */
    function getFormContext(formContext) {
        var ctx = { caseId: "", accountId: "", accountName: "", serialNumber: "" };
        var entityName = formContext.data.entity.getEntityName();

        // Account form — the record itself is the account
        if (entityName === "account") {
            ctx.accountId = formContext.data.entity.getId().replace(/[{}]/g, "");
            var nameAttr = formContext.getAttribute("name");
            if (nameAttr) { ctx.accountName = nameAttr.getValue() || ""; }
            return ctx;
        }

        // Case — get both the case ID and the customer account
        if (entityName === "incident") {
            ctx.caseId = formContext.data.entity.getId().replace(/[{}]/g, "");
            var customer = formContext.getAttribute("customerid");
            if (customer) {
                var cVal = customer.getValue();
                if (cVal && cVal.length > 0 && cVal[0].entityType === "account") {
                    ctx.accountId = cVal[0].id.replace(/[{}]/g, "");
                    ctx.accountName = cVal[0].name || "";
                }
            }
            var serialAttr = formContext.getAttribute("productserialnumber");
            if (serialAttr) { ctx.serialNumber = serialAttr.getValue() || ""; }
            return ctx;
        }

        // Phone Call — regardingobjectid
        if (entityName === "phonecall") {
            var regarding = formContext.getAttribute("regardingobjectid");
            if (regarding) {
                var rVal = regarding.getValue();
                if (rVal && rVal.length > 0 && rVal[0].entityType === "account") {
                    ctx.accountId = rVal[0].id.replace(/[{}]/g, "");
                    ctx.accountName = rVal[0].name || "";
                }
                if (rVal && rVal.length > 0 && rVal[0].entityType === "incident") {
                    ctx.caseId = rVal[0].id.replace(/[{}]/g, "");
                }
            }
        }

        // Active Conversation — try customer context
        if (entityName === "msdyn_ocliveworkitem") {
            var acctLookup = formContext.getAttribute("msdyn_customer");
            if (acctLookup) {
                var aVal = acctLookup.getValue();
                if (aVal && aVal.length > 0 && aVal[0].entityType === "account") {
                    ctx.accountId = aVal[0].id.replace(/[{}]/g, "");
                    ctx.accountName = aVal[0].name || "";
                }
            }
        }

        return ctx;
    }

    /**
     * Build the Custom Page navigation target, encoding
     * caseId, accountId, accountName, and serialNumber as a
     * pipe-delimited recordId string so the Custom Page can
     * parse all four values.
     * Format: "accountId|caseId|accountName|serialNumber"
     */
    function buildPageNav(ctx) {
        var nav = {
            pageType: "custom",
            name: PAGE_NAME
        };
        // Encode as "accountId|caseId|accountName|serialNumber"
        var composite = (ctx.accountId || "") + "|" +
            (ctx.caseId || "") + "|" +
            (ctx.accountName || "") + "|" +
            (ctx.serialNumber || "");
        if (ctx.accountId || ctx.caseId) {
            nav.recordId = composite;
        }
        return nav;
    }

    /**
     * Form OnLoad handler.
     * Creates (or re-navigates) the Service Toolkit side pane,
     * passing account ID, case ID, account name, and serial
     * number for the Custom Page to use across all screens.
     * @param {object} executionContext - Form execution context
     */
    BW.ServiceToolkit.onLoad = function (executionContext) {
        try {
            var formCtx = executionContext.getFormContext();
            var ctx = getFormContext(formCtx);
            var pageNav = buildPageNav(ctx);

            var existingPane = parent.Xrm.App.sidePanes.getPane(PANE_ID);

            if (existingPane == undefined || existingPane == null) {
                // Create the pane for the first time
                parent.Xrm.App.sidePanes.createPane({
                    title: PANE_TITLE,
                    imageSrc: PANE_ICON,
                    paneId: PANE_ID,
                    width: PANE_WIDTH,
                    canClose: true,
                    alwaysRender: true
                }).then(function (pane) {
                    pane.navigate(pageNav);
                }).catch(function (err) {
                    console.error("[ServiceToolkit] createPane error:", err);
                });
            } else {
                // Pane exists – just re-navigate to refresh
                existingPane.navigate(pageNav);
            }
        } catch (e) {
            console.error("[ServiceToolkit] onLoad error:", e.message);
        }
    };

})();
