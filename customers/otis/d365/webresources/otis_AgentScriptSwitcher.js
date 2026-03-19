/**
 * Otis Agent Script Switcher
 * Auto-selects the appropriate agent script based on case attributes.
 * 
 * Web Resource Name: otis_AgentScriptSwitcher
 * Add to Case form OnLoad event
 * 
 * Configuration requires:
 * 1. Agent Scripts created and Active in Customer Service admin center
 * 2. Scripts associated with Session Template (see below)
 * 3. This JS added to Case form OnLoad
 */

var Otis = Otis || {};
Otis.AgentScript = Otis.AgentScript || {};

(function () {
    "use strict";

    // ============================================================
    // CONFIGURATION - Update these GUIDs after creating scripts
    // ============================================================
    // Get these IDs from: Customer Service admin center > Agent Scripts > Open script > URL contains the ID
    
    const SCRIPT_CONFIG = {
        // Entrapment Response Protocol (SCRIPT-001)
        entrapmentScript: {
            name: "Entrapment Response Protocol (SCRIPT-001)",
            id: null, // TODO: Get from D365 - check msdyn_productivityagentscripts table
            uniqueName: "otis_entrapmentresponseprotocol"
        },
        // Service Request Intake (SCRIPT-002)  
        serviceRequestScript: {
            name: "Service Request Intake (SCRIPT-002)",
            id: null, // TODO: Get from D365
            uniqueName: "otis_servicerequestintake"
        },
        // Default fallback script
        defaultScript: {
            name: "Case agent script",
            id: null,
            uniqueName: "msdyn_caseagentscript"
        }
    };

    // Case Type values that trigger Entrapment script
    const ENTRAPMENT_TYPES = [
        "Entrapment",
        "Passenger Trapped",
        "Emergency - Entrapment"
    ];

    // Priority values that also trigger Entrapment script
    const CRITICAL_PRIORITIES = [1]; // 1 = Critical/Immediate

    // ============================================================
    // MAIN FUNCTIONS
    // ============================================================

    /**
     * Form OnLoad handler - determines and sets appropriate agent script
     */
    Otis.AgentScript.onLoad = function (executionContext) {
        var formContext = executionContext.getFormContext();
        
        // Only run in Customer Service Workspace (not web client)
        if (!Xrm.App || !Xrm.App.sidePanes) {
            console.log("Otis.AgentScript: Not in CSW workspace - skipping");
            return;
        }

        try {
            var scriptToSelect = determineAgentScript(formContext);
            console.log("Otis.AgentScript: Determined script - " + scriptToSelect.name);
            
            // Attempt to set the agent script
            setAgentScript(scriptToSelect);
            
        } catch (error) {
            console.error("Otis.AgentScript.onLoad error: " + error.message);
        }
    };

    /**
     * Determines which agent script to use based on case attributes
     */
    function determineAgentScript(formContext) {
        // Get case type
        var caseTypeAttr = formContext.getAttribute("casetypecode");
        var caseType = caseTypeAttr ? caseTypeAttr.getText() : null;
        
        // Get priority
        var priorityAttr = formContext.getAttribute("prioritycode");
        var priority = priorityAttr ? priorityAttr.getValue() : null;
        
        // Get custom case type field if you have one
        var customTypeAttr = formContext.getAttribute("new_casetype") || formContext.getAttribute("otis_casetype");
        var customType = customTypeAttr ? customTypeAttr.getText() : null;

        console.log("Otis.AgentScript: Case Type = " + caseType + ", Priority = " + priority + ", Custom Type = " + customType);

        // Logic: Check for entrapment conditions
        if (isEntrapmentCase(caseType, customType, priority)) {
            return SCRIPT_CONFIG.entrapmentScript;
        }

        // Default to Service Request Intake for all other cases
        return SCRIPT_CONFIG.serviceRequestScript;
    }

    /**
     * Checks if case qualifies for Entrapment Response Protocol
     */
    function isEntrapmentCase(caseType, customType, priority) {
        // Check case type text
        if (caseType && ENTRAPMENT_TYPES.some(t => caseType.toLowerCase().includes(t.toLowerCase()))) {
            return true;
        }
        
        // Check custom case type
        if (customType && ENTRAPMENT_TYPES.some(t => customType.toLowerCase().includes(t.toLowerCase()))) {
            return true;
        }

        // Check for critical priority
        if (priority && CRITICAL_PRIORITIES.includes(priority)) {
            return true;
        }

        return false;
    }

    /**
     * Sets the agent script in the productivity pane
     * Note: This uses internal APIs that may change between releases
     */
    function setAgentScript(scriptConfig) {
        // Method 1: Try using the Productivity Tools API (if available)
        if (window.Microsoft && Microsoft.ProductivityTools) {
            try {
                Microsoft.ProductivityTools.setActiveAgentScript(scriptConfig.id || scriptConfig.uniqueName);
                console.log("Otis.AgentScript: Set via ProductivityTools API");
                return;
            } catch (e) {
                console.log("Otis.AgentScript: ProductivityTools API not available");
            }
        }

        // Method 2: Try using session context (CSW specific)
        if (Xrm.App && Xrm.App.sessions) {
            try {
                var focusedSession = Xrm.App.sessions.getFocusedSession();
                if (focusedSession && focusedSession.tabs) {
                    // The agent script pane is typically a tab in the session
                    console.log("Otis.AgentScript: Found session - attempting to set script");
                    // Note: Direct API to set agent script may require custom solution
                }
            } catch (e) {
                console.log("Otis.AgentScript: Session API error - " + e.message);
            }
        }

        // Method 3: Store preference for manual selection prompt
        // This at least tells the agent which script to select
        try {
            sessionStorage.setItem("otis_recommendedScript", JSON.stringify({
                name: scriptConfig.name,
                reason: "Based on case type/priority"
            }));
            console.log("Otis.AgentScript: Stored recommendation for " + scriptConfig.name);
        } catch (e) {
            // Ignore storage errors
        }
    }

    /**
     * Field OnChange handler - re-evaluates when case type or priority changes
     */
    Otis.AgentScript.onCaseTypeChange = function (executionContext) {
        var formContext = executionContext.getFormContext();
        var scriptToSelect = determineAgentScript(formContext);
        
        // Show notification to agent
        formContext.ui.setFormNotification(
            "Recommended script: " + scriptToSelect.name,
            "INFO",
            "agentScriptRecommendation"
        );
        
        // Clear after 5 seconds
        setTimeout(function() {
            formContext.ui.clearFormNotification("agentScriptRecommendation");
        }, 5000);
    };

})();

/**
 * SETUP INSTRUCTIONS:
 * ==================
 * 
 * 1. Create Web Resource:
 *    - Go to: Power Apps > Solutions > Your Solution > New > Web Resource
 *    - Name: otis_AgentScriptSwitcher
 *    - Type: JavaScript (JS)
 *    - Upload this file
 *    - Publish
 * 
 * 2. Add to Case Form:
 *    - Open Case entity > Forms > Case for Multisession experience
 *    - Form Properties > Add Library > otis_AgentScriptSwitcher
 *    - Event Handlers > OnLoad > Add:
 *      - Library: otis_AgentScriptSwitcher
 *      - Function: Otis.AgentScript.onLoad
 *      - Pass execution context: Yes
 *    - Save and Publish
 * 
 * 3. (Optional) Add OnChange handler:
 *    - Case Type field > Events > OnChange > Add:
 *      - Library: otis_AgentScriptSwitcher
 *      - Function: Otis.AgentScript.onCaseTypeChange
 *      - Pass execution context: Yes
 * 
 * 4. Associate Scripts with Session Template:
 *    - Customer Service admin center > Workspaces > Session templates
 *    - Edit "Case session - default" (or your custom template)
 *    - Agent scripts tab > Add your scripts
 *    - This makes them appear in the dropdown
 * 
 * 5. Get Agent Script IDs:
 *    - Run this in browser console while on D365:
 *    Xrm.WebApi.retrieveMultipleRecords("msdyn_productivityagentscript", 
 *        "?$select=msdyn_name,msdyn_productivityagentscriptid&$filter=statecode eq 0"
 *    ).then(r => console.table(r.entities));
 */
