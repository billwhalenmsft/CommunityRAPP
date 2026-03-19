/**
 * Otis Case Form Scripts
 * 
 * 1. Auto-sets Priority based on Case Type selection
 * 2. Hot Word Notification banners (entrapment, safety, etc.)
 * 3. Auto-sets Tier Level (cr377_tierlevel) from account tier / hot words
 * 4. Auto-sets Incident Type from title keyword detection
 * 
 * Web Resource Name: bw_OtisCaseFormScripts
 * Add to Case form OnLoad: Otis.Case.onLoad
 * Pass execution context: Yes
 */

var Otis = Otis || {};
Otis.Case = Otis.Case || {};

(function () {
    "use strict";

    // ============================================================
    // CONFIGURATION - Case Type to Priority Mapping
    // ============================================================
    // Case Type values: 1 = Question, 2 = Problem, 3 = Request
    // Priority values:  1 = High, 2 = Normal, 3 = Low
    var CASE_TYPE_PRIORITY_MAP = {
        2: 1,   // Problem -> High
        3: 2,   // Request -> Normal
        1: 2    // Question -> Normal
    };

    var CASE_TYPE_LABELS = {
        1: "Question",
        2: "Problem",
        3: "Request"
    };

    var PRIORITY_LABELS = {
        1: "High",
        2: "Normal",
        3: "Low"
    };

    // ============================================================
    // HOT WORD CONFIGURATION
    // ============================================================
    // Critical = RED banner (immediate safety / life-safety)
    var CRITICAL_WORDS = ["entrapment", "trapped", "stuck", "injury", "injured", "emergency", "fire"];
    // High = YELLOW banner (urgent service)
    var HIGH_WORDS = ["out of service", "not working", "stopped", "safety inspection", "complaint"];

    // ============================================================
    // TIER LEVEL CONFIGURATION (cr377_tierlevel)
    // ============================================================
    var TIER_FIELD = "cr377_tierlevel";
    var TIER_1 = 192350000;  // Strategic / Hot Word (RED)
    var TIER_2 = 192350001;  // Key Account (ORANGE)
    // var TIER_3 = 192350002;  // Standard (BLUE)
    // var TIER_4 = 192350003;  // Basic (GRAY)

    // ============================================================
    // INCIDENT TYPE KEYWORD MAPPING
    // ============================================================
    // Maps title keywords to incident type names for Xrm.WebApi lookup.
    // Requires msdyn_primaryincidenttype field on Case (Field Service).
    // If the field is not present, this feature is safely skipped.
    // First match wins, so order matters (most specific first).
    var INCIDENT_TYPE_KEYWORDS = [
        { keywords: ["entrapment", "trapped", "stuck in elevator"],  name: "Entrapment" },
        { keywords: ["out of service", "not working", "stopped"],    name: "Unit Out of Service" },
        { keywords: ["door issue", "door alignment", "door sensor"], name: "Door Issue" },
        { keywords: ["noise", "vibration"],                          name: "Noise/Vibration Complaint" },
        { keywords: ["scheduled maintenance", "preventive maintenance", "quarterly maintenance"], name: "Scheduled Maintenance" },
        { keywords: ["billing", "invoice", "charges"],               name: "Billing Inquiry" },
        { keywords: ["contract question", "contract coverage", "renewal"], name: "Contract Question" },
        { keywords: ["modernization", "upgrade"],                    name: "Modernization Request" }
    ];

    // ============================================================
    // FORM ONLOAD
    // ============================================================
    Otis.Case.onLoad = function (executionContext) {
        var formContext = executionContext.getFormContext();

        // Register onChange for Case Type
        var caseTypeAttr = formContext.getAttribute("casetypecode");
        if (caseTypeAttr) {
            caseTypeAttr.addOnChange(Otis.Case.onCaseTypeChange);
        }

        // Register hot word detection on title and description
        var titleAttr = formContext.getAttribute("title");
        if (titleAttr) {
            titleAttr.addOnChange(Otis.Case._checkHotWords);
            titleAttr.addOnChange(Otis.Case._autoSetIncidentType);
        }
        var descAttr = formContext.getAttribute("description");
        if (descAttr) {
            descAttr.addOnChange(Otis.Case._checkHotWords);
        }

        // Run hot word check on load (for existing cases)
        Otis.Case._checkHotWords(executionContext);

        // Auto-set tier from account on load (if not already set)
        Otis.Case._setTierFromAccount(formContext);

        console.log("Otis.Case: Form loaded - case type + hot word + tier + incident type handlers registered");
    };

    // ============================================================
    // CASE TYPE ONCHANGE - Auto-set Priority
    // ============================================================
    Otis.Case.onCaseTypeChange = function (executionContext) {
        var formContext = executionContext.getFormContext();

        var caseTypeAttr = formContext.getAttribute("casetypecode");
        if (!caseTypeAttr) return;

        var caseTypeVal = caseTypeAttr.getValue();
        if (!caseTypeVal) return;

        console.log("Otis.Case: Case Type changed to: " + CASE_TYPE_LABELS[caseTypeVal]);

        var newPriority = CASE_TYPE_PRIORITY_MAP[caseTypeVal];
        if (newPriority) {
            var priorityAttr = formContext.getAttribute("prioritycode");
            if (priorityAttr) {
                var currentPriority = priorityAttr.getValue();
                if (currentPriority !== newPriority) {
                    priorityAttr.setValue(newPriority);

                    formContext.ui.setFormNotification(
                        "Priority set to " + PRIORITY_LABELS[newPriority] +
                        " based on case type: " + CASE_TYPE_LABELS[caseTypeVal],
                        "INFO",
                        "otis_priorityAutoSet"
                    );

                    setTimeout(function () {
                        formContext.ui.clearFormNotification("otis_priorityAutoSet");
                    }, 5000);

                    console.log("Otis.Case: Priority → " + PRIORITY_LABELS[newPriority]);
                }
            }
        }
    };

    // ============================================================
    // HOT WORD NOTIFICATION - Tiered Severity Banners
    // ============================================================
    Otis.Case._checkHotWords = function (executionContext) {
        var formContext;
        if (executionContext && executionContext.getFormContext) {
            formContext = executionContext.getFormContext();
        } else {
            return;
        }

        var titleAttr = formContext.getAttribute("title");
        var descAttr = formContext.getAttribute("description");
        var titleVal = ((titleAttr && titleAttr.getValue()) || "").toLowerCase();
        var descVal = ((descAttr && descAttr.getValue()) || "").toLowerCase();
        var combined = titleVal + " " + descVal;

        var criticalDetected = [];
        var highDetected = [];
        var i;

        for (i = 0; i < CRITICAL_WORDS.length; i++) {
            if (combined.indexOf(CRITICAL_WORDS[i]) >= 0) {
                criticalDetected.push(CRITICAL_WORDS[i].toUpperCase());
            }
        }
        for (i = 0; i < HIGH_WORDS.length; i++) {
            if (combined.indexOf(HIGH_WORDS[i]) >= 0) {
                highDetected.push(HIGH_WORDS[i].toUpperCase());
            }
        }

        // Clear previous hot word notifications
        formContext.ui.clearFormNotification("otis_hotword_critical");
        formContext.ui.clearFormNotification("otis_hotword_high");

        if (criticalDetected.length > 0) {
            formContext.ui.setFormNotification(
                "🚨 EMERGENCY ALERT: " + criticalDetected.join(", ") +
                " detected — This case requires IMMEDIATE action. " +
                "Follow Entrapment Response Protocol. Dispatch emergency technician.",
                "ERROR",
                "otis_hotword_critical"
            );
        }

        if (highDetected.length > 0) {
            formContext.ui.setFormNotification(
                "⚠️ PRIORITY ESCALATION: " + highDetected.join(", ") +
                " detected — This case has been flagged for urgent attention. " +
                "Priority and severity set to HIGH.",
                "WARNING",
                "otis_hotword_high"
            );
        }

        // Auto-escalate if any hot words found
        if (criticalDetected.length > 0 || highDetected.length > 0) {
            var priority = formContext.getAttribute("prioritycode");
            if (priority && priority.getValue() !== 1) {
                priority.setValue(1);
            }

            var escalated = formContext.getAttribute("isescalated");
            if (escalated && !escalated.getValue()) {
                escalated.setValue(true);
            }

            var severity = formContext.getAttribute("severitycode");
            if (severity && severity.getValue() !== 1) {
                severity.setValue(1);
            }

            // Set Tier Level to Tier 1 (hot words always = Tier 1)
            var tierLevel = formContext.getAttribute(TIER_FIELD);
            if (tierLevel && tierLevel.getValue() !== TIER_1) {
                tierLevel.setValue(TIER_1);
                console.log("Otis.Case: Tier Level -> Tier 1 (hot word detected)");
            }
        }
    };

    // ============================================================
    // TIER LEVEL - Set from Account (on load, if not already set)
    // ============================================================
    Otis.Case._setTierFromAccount = function (formContext) {
        var tierAttr = formContext.getAttribute(TIER_FIELD);
        if (!tierAttr) return;

        // If tier already set (e.g., by hot word or previous save), leave it
        if (tierAttr.getValue() !== null) return;

        // Look up the parent account's description for tier info
        var customerAttr = formContext.getAttribute("customerid");
        if (!customerAttr) return;
        var customerVal = customerAttr.getValue();
        if (!customerVal || customerVal.length === 0) return;

        var customerId = customerVal[0].id.replace("{", "").replace("}", "");
        var entityType = customerVal[0].entityType;
        if (entityType !== "account") return;

        Xrm.WebApi.retrieveRecord("account", customerId, "?$select=description").then(
            function (account) {
                var desc = (account.description || "").toLowerCase();
                var tier = null;

                if (desc.indexOf("tier: 1") >= 0 || desc.indexOf("tier 1") >= 0) {
                    tier = TIER_1;
                } else if (desc.indexOf("tier: 2") >= 0 || desc.indexOf("tier 2") >= 0) {
                    tier = TIER_2;
                }

                if (tier !== null && tierAttr.getValue() !== tier) {
                    tierAttr.setValue(tier);
                    console.log("Otis.Case: Tier Level set from account description");
                }
            },
            function (error) {
                console.log("Otis.Case: Could not read account for tier: " + error.message);
            }
        );
    };

    // ============================================================
    // INCIDENT TYPE - Auto-set from title keywords
    // ============================================================
    Otis.Case._autoSetIncidentType = function (executionContext) {
        var formContext;
        if (executionContext && executionContext.getFormContext) {
            formContext = executionContext.getFormContext();
        } else {
            return;
        }

        // Only auto-set if incident type is not already set
        var incidentTypeAttr = formContext.getAttribute("msdyn_primaryincidenttype");
        if (!incidentTypeAttr) return;
        if (incidentTypeAttr.getValue() !== null) return;

        var titleAttr = formContext.getAttribute("title");
        if (!titleAttr) return;
        var titleVal = (titleAttr.getValue() || "").toLowerCase();
        if (!titleVal) return;

        // Find first matching incident type
        var matchedName = null;
        for (var m = 0; m < INCIDENT_TYPE_KEYWORDS.length; m++) {
            var entry = INCIDENT_TYPE_KEYWORDS[m];
            for (var k = 0; k < entry.keywords.length; k++) {
                if (titleVal.indexOf(entry.keywords[k]) >= 0) {
                    matchedName = entry.name;
                    break;
                }
            }
            if (matchedName) break;
        }

        if (!matchedName) return;

        // Look up the incident type ID via WebApi
        var filter = "?$select=msdyn_incidenttypeid,msdyn_name&$filter=msdyn_name eq '" + matchedName + "'";
        Xrm.WebApi.retrieveMultipleRecords("msdyn_incidenttype", filter).then(
            function (results) {
                if (results.entities.length > 0) {
                    var record = results.entities[0];
                    // Double-check it's still empty (async timing)
                    if (incidentTypeAttr.getValue() === null) {
                        incidentTypeAttr.setValue([{
                            id: record.msdyn_incidenttypeid,
                            name: record.msdyn_name,
                            entityType: "msdyn_incidenttype"
                        }]);
                        console.log("Otis.Case: Incident Type -> " + record.msdyn_name + " (from title keyword)");
                    }
                }
            },
            function (error) {
                console.log("Otis.Case: Incident type lookup failed: " + error.message);
            }
        );
    };

})();

/**
 * SETUP INSTRUCTIONS:
 * ==================
 * 
 * 1. Update Web Resource in D365:
 *    - Solution > Demo Components > bw_OtisCaseFormScripts
 *    - Upload this file, Save, Publish
 * 
 * 2. Add to Case Form (Enhanced Full Case Form):
 *    - Form Properties > Form Libraries > Add "bw_OtisCaseFormScripts"
 *    - OnLoad event > + Event handler:
 *      Library: bw_OtisCaseFormScripts
 *      Function: Otis.Case.onLoad
 *      Pass execution context: YES
 *    - Save and Publish form
 * 
 * 3. Ensure these fields are on the form:
 *    - Case Type (casetypecode)
 *    - Priority (prioritycode)
 *    - Tier Level (cr377_tierlevel)
 *    - Primary Incident Type (msdyn_primaryincidenttype)
 *    - Is Escalated (isescalated)
 * 
 * BEHAVIORS:
 * ==========
 * 
 * Case Type -> Priority:
 *   Problem  (2) -> High (1)
 *   Request  (3) -> Normal (2)
 *   Question (1) -> Normal (2)
 * 
 * Hot Word Banners (scans title + description):
 *   RED (CRITICAL):  entrapment, trapped, stuck, injury, injured, emergency, fire
 *   YELLOW (HIGH):   out of service, not working, stopped, safety inspection, complaint
 *   Hot words auto-set: Priority=High, Severity=High, Escalated=Yes, Tier=1
 * 
 * Tier Level (cr377_tierlevel):
 *   Auto-set from account description on load (Tier 1 or Tier 2)
 *   Hot words always override to Tier 1
 * 
 * Incident Type (msdyn_primaryincidenttype):
 *   Auto-set from title keywords when field is empty:
 *   entrapment/trapped/stuck    -> Entrapment
 *   out of service/not working  -> Unit Out of Service
 *   door issue/alignment/sensor -> Door Issue
 *   noise/vibration             -> Noise/Vibration Complaint
 *   maintenance/scheduled       -> Scheduled Maintenance
 *   billing/invoice             -> Billing Inquiry
 *   contract question/coverage  -> Contract Question
 *   modernization/upgrade       -> Modernization Request
 */
