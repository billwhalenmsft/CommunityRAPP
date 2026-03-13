<#
.SYNOPSIS
    Step 24: Create QM Evaluation Criteria, Sections, Questions, and Evaluation Plans
.DESCRIPTION
    Creates the "Manufacturing Service Quality Standard" evaluation criteria with
    6 sections, 21 questions (all AI-enabled), a criteria version with scoring,
    publishes the criteria, and creates two evaluation plans.
.NOTES
    Entities: msdyn_evaluationcriteria, msdyn_evaluationcategory,
              msdyn_evaluationquestion, msdyn_evaluationcriteriaversion,
              msdyn_evaluationplan
    Safe to re-run (uses Find-OrCreate-Record for all records).
#>

param()

# ============================================================
# Module Import & Connection
# ============================================================
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force
Connect-Dataverse
Write-StepHeader "24" "QM Evaluation Criteria & Plans"

# Helper to escape single quotes in OData filter strings
function Escape-OData([string]$text) { $text -replace "'", "''" }

# ============================================================
# DATA DEFINITION
# ============================================================

$CriteriaName = "Manufacturing Service Quality Standard"
$CriteriaDescription = "Standard quality evaluation criteria for discrete manufacturing customer service. Evaluates agent performance across customer handling, technical accuracy, process compliance, resolution quality, communication, and tool adoption."

$FormInstructions = @"
Evaluate the agent's performance on this customer service interaction for a discrete manufacturing company. The company serves distributors, contractors, and end-users through email and phone channels with a tiered customer model (Tier 1 = Strategic / highest priority through Tier 4 = Basic). 

Agents are expected to: verify customer identity, reference product knowledge, follow escalation procedures for safety and compliance terms (hot words: Urgent, Emergency, Recall, Safety, Legal, Next Day Air), meet SLA targets, document resolutions thoroughly, and leverage AI tools (Copilot, knowledge base) where available. 

Score based on what is observable in the case notes, conversation transcript, and case metadata. If a question does not apply to the interaction, select the neutral or "Not applicable" option.
"@

# Question types
$YesNo = 700610000
$ChooseList = 700610002

# ----- Section definitions with questions and answer options -----
$Sections = @(
    # ===== Section 1: Customer Identification & Account Handling =====
    @{
        Name        = "Customer Identification & Account Handling"
        Description = "Evaluates whether the agent properly identified the customer, verified account details, and recognized the customer's service tier and entitlement status."
        Weight      = 15
        Questions   = @(
            @{
                Text         = "Did the agent verify the customer's identity and account?"
                Type         = $YesNo
                Instructions = "Check if the agent confirmed the customer name, account, and contact information at the beginning of the interaction. Look for evidence in case notes or conversation transcript."
                Options      = @(
                    @{ Label = "Yes"; Score = 100; Desc = "Agent confirmed customer identity, account name, and/or contact details." }
                    @{ Label = "No"; Score = 0; Desc = "Agent did not verify customer identity or account information before proceeding." }
                )
            },
            @{
                Text         = "Did the agent identify the customer's service tier or priority level?"
                Type         = $YesNo
                Instructions = "Check if the agent acknowledged or acted upon the customer's tier level (e.g., Strategic, Key, Standard, Basic). This may be evident from routing priority, SLA handling, or explicit mention in notes."
                Options      = @(
                    @{ Label = "Yes"; Score = 100; Desc = "Agent acknowledged or acted on the customer's service tier (e.g., prioritized a Tier 1 account, followed standard process for Tier 3)." }
                    @{ Label = "No"; Score = 0; Desc = "No evidence that the agent recognized or acted on the customer's service tier." }
                )
            },
            @{
                Text         = "Did the agent check entitlement or warranty status when relevant?"
                Type         = $ChooseList
                Instructions = "If the interaction involved a product issue, return request, or warranty claim, the agent should have checked the customer's entitlement or warranty status. Select 'Not applicable' if the interaction did not require entitlement verification."
                Options      = @(
                    @{ Label = "Verified entitlement"; Score = 100; Desc = "Agent checked and confirmed the customer's entitlement, warranty, or service agreement status." }
                    @{ Label = "Did not verify (should have)"; Score = 0; Desc = "The interaction warranted an entitlement check but the agent did not perform one." }
                    @{ Label = "Not applicable"; Score = 50; Desc = "The interaction did not involve product issues, returns, or warranty claims." }
                )
            }
        )
    },

    # ===== Section 2: Technical Accuracy & Product Knowledge =====
    @{
        Name        = "Technical Accuracy & Product Knowledge"
        Description = "Evaluates the agent's product knowledge, accuracy of technical information provided, and appropriate use of knowledge articles and documentation."
        Weight      = 25
        Questions   = @(
            @{
                Text         = "Did the agent demonstrate accurate product knowledge?"
                Type         = $ChooseList
                Instructions = "Evaluate whether the agent correctly referenced product names, part numbers, specifications, compatibility information, or technical procedures. Look for accuracy in the information provided to the customer."
                Options      = @(
                    @{ Label = "Demonstrated strong product knowledge"; Score = 100; Desc = "Agent referenced specific product details, specs, or part numbers accurately and confidently." }
                    @{ Label = "Adequate product knowledge"; Score = 66; Desc = "Agent provided generally correct information but lacked specificity or depth." }
                    @{ Label = "Product knowledge gaps observed"; Score = 0; Desc = "Agent provided incorrect product information or could not answer basic product questions." }
                    @{ Label = "Unable to assess"; Score = 50; Desc = "The interaction did not require product-specific knowledge." }
                )
            },
            @{
                Text         = "Did the agent reference relevant knowledge articles or documentation?"
                Type         = $YesNo
                Instructions = "Check if the agent searched for and referenced internal knowledge articles, technical documentation, or standard operating procedures. Evidence includes KB article links in case notes, Copilot suggestions accepted, or documented references to procedures."
                Options      = @(
                    @{ Label = "Yes"; Score = 100; Desc = "Agent referenced or linked at least one knowledge article, technical document, or SOP during the interaction." }
                    @{ Label = "No"; Score = 0; Desc = "No evidence that the agent consulted the knowledge base or referenced documentation." }
                )
            },
            @{
                Text         = "Was the technical diagnosis or troubleshooting approach appropriate?"
                Type         = $ChooseList
                Instructions = "For technical issues, evaluate whether the agent followed a logical troubleshooting sequence, asked the right questions, and worked toward identifying the correct root cause. Consider whether the agent gathered sufficient information before proposing a solution."
                Options      = @(
                    @{ Label = "Systematic and thorough diagnosis"; Score = 100; Desc = "Agent followed a logical troubleshooting process, asked appropriate clarifying questions, and correctly identified the issue." }
                    @{ Label = "Adequate diagnosis"; Score = 66; Desc = "Agent made a reasonable attempt at diagnosis but missed some steps or questions." }
                    @{ Label = "Incomplete or incorrect diagnosis"; Score = 0; Desc = "Agent jumped to conclusions, skipped key troubleshooting steps, or arrived at an incorrect diagnosis." }
                    @{ Label = "No diagnosis required"; Score = 50; Desc = "The interaction did not involve a technical issue requiring diagnosis (e.g., order status inquiry)." }
                )
            },
            @{
                Text         = "Did the agent provide accurate part numbers, specs, or compatibility info?"
                Type         = $ChooseList
                Instructions = "If the customer asked about specific parts, replacement components, or product compatibility, evaluate whether the agent's response was accurate. Select 'Not applicable' if no specific part or specification information was requested."
                Options      = @(
                    @{ Label = "Accurate information provided"; Score = 100; Desc = "Agent provided correct part numbers, specifications, or compatibility information." }
                    @{ Label = "Inaccurate information provided"; Score = 0; Desc = "Agent provided incorrect part numbers, specs, or compatibility data." }
                    @{ Label = "Not applicable"; Score = 50; Desc = "No specific part or specification information was requested during the interaction." }
                )
            }
        )
    },

    # ===== Section 3: Process Compliance & Escalation Handling =====
    @{
        Name        = "Process Compliance & Escalation Handling"
        Description = "Evaluates adherence to standard operating procedures, proper handling of escalation triggers (hot words, safety terms), and compliance with organizational policies."
        Weight      = 20
        Questions   = @(
            @{
                Text         = "Did the agent follow the standard case handling procedure?"
                Type         = $YesNo
                Instructions = "Evaluate whether the agent followed the expected workflow: greeting, verification, issue capture, investigation, resolution, documentation, and closure. Check that required fields were populated and case notes are complete."
                Options      = @(
                    @{ Label = "Yes"; Score = 100; Desc = "Agent followed the standard case handling workflow and populated required fields." }
                    @{ Label = "No"; Score = 0; Desc = "Agent skipped key process steps, left required fields empty, or deviated from the expected workflow." }
                )
            },
            @{
                Text         = "Were escalation triggers (hot words) handled appropriately?"
                Type         = $ChooseList
                Instructions = "Check if the interaction contained priority keywords such as 'urgent', 'emergency', 'recall', 'safety', 'legal', or 'next day air'. If present, verify the agent escalated or adjusted priority per the hot word policy. If no triggers were present, select 'No escalation triggers present'."
                Options      = @(
                    @{ Label = "Correctly identified and escalated"; Score = 100; Desc = "Agent detected the escalation keyword and took appropriate action (priority boost, supervisor notification, or tier escalation)." }
                    @{ Label = "Missed an escalation trigger"; Score = 0; Desc = "An escalation trigger was present in the interaction but the agent did not escalate or adjust priority." }
                    @{ Label = "Escalated unnecessarily"; Score = 33; Desc = "Agent escalated when no trigger or business justification existed." }
                    @{ Label = "No escalation triggers present"; Score = 50; Desc = "The interaction did not contain any escalation keywords or scenarios requiring escalation." }
                )
            },
            @{
                Text         = "Did the agent route or escalate to the correct team?"
                Type         = $ChooseList
                Instructions = "If the case required escalation to a specialist, supervisor, or different team, evaluate whether the agent chose the correct destination. Consider brand alignment (correct product team), skill requirements, and tier-based routing rules."
                Options      = @(
                    @{ Label = "Correctly routed or escalated"; Score = 100; Desc = "Agent escalated to the appropriate team, specialist, or supervisor based on the issue type and routing rules." }
                    @{ Label = "Routed to wrong team"; Score = 0; Desc = "Agent escalated but sent the case to the wrong team or specialist." }
                    @{ Label = "Should have escalated but did not"; Score = 0; Desc = "The issue warranted escalation but the agent attempted to resolve it beyond their capability." }
                    @{ Label = "No routing change needed"; Score = 50; Desc = "The agent was the appropriate owner and no escalation was required." }
                )
            },
            @{
                Text         = "Were safety, recall, or compliance concerns addressed per policy?"
                Type         = $YesNo
                Instructions = "If the interaction involved safety concerns, product recalls, regulatory issues, or compliance-sensitive topics, check that the agent followed the required procedures (documentation, notifications, escalation to appropriate team). Answer 'Yes' if no safety/compliance topics were involved or if they were handled correctly."
                Options      = @(
                    @{ Label = "Yes"; Score = 100; Desc = "No safety/compliance issues were involved, OR the agent handled them correctly per policy." }
                    @{ Label = "No"; Score = 0; Desc = "Safety, recall, or compliance concerns were present but the agent did not follow the required procedures." }
                )
            }
        )
    },

    # ===== Section 4: Resolution Effectiveness =====
    @{
        Name        = "Resolution Effectiveness"
        Description = "Evaluates the quality of the resolution provided, root cause identification, documentation completeness, and follow-up actions."
        Weight      = 20
        Questions   = @(
            @{
                Text         = "How effectively was the customer's issue resolved?"
                Type         = $ChooseList
                Instructions = "Evaluate the final outcome of the interaction. 'Fully resolved on first contact' means the customer's issue was completely addressed in a single interaction. 'Resolved with follow-up' means the issue is resolved but required or scheduled additional actions."
                Options      = @(
                    @{ Label = "Fully resolved on first contact"; Score = 100; Desc = "Customer's issue was completely addressed in this interaction with no further action needed." }
                    @{ Label = "Resolved with follow-up needed"; Score = 75; Desc = "Issue is being addressed but requires scheduled follow-up (e.g., replacement shipment, engineering review, callback)." }
                    @{ Label = "Partially resolved"; Score = 50; Desc = "Some aspects of the customer's issue were addressed but significant items remain open." }
                    @{ Label = "Not resolved"; Score = 0; Desc = "The customer's issue was not addressed or the agent was unable to provide a solution." }
                    @{ Label = "Case still in progress"; Score = 50; Desc = "The case is still actively being worked and resolution has not yet been attempted." }
                )
            },
            @{
                Text         = "Did the agent identify the root cause of the issue?"
                Type         = $YesNo
                Instructions = "Check if the agent documented the underlying cause of the customer's problem, not just the symptom. Root cause analysis helps prevent recurrence and builds the knowledge base. For non-technical inquiries (e.g., order status), answer 'Yes' if the agent identified the reason for the inquiry."
                Options      = @(
                    @{ Label = "Yes"; Score = 100; Desc = "Agent identified and documented the root cause or underlying reason for the customer's issue." }
                    @{ Label = "No"; Score = 0; Desc = "Agent resolved the symptom but did not identify or document the root cause." }
                )
            },
            @{
                Text         = "Was the case documentation thorough and complete?"
                Type         = $ChooseList
                Instructions = "Evaluate the completeness of case notes, resolution description, and any attached documentation. Good documentation should enable another agent to understand the issue, what was tried, and how it was resolved without needing to contact the customer again."
                Options      = @(
                    @{ Label = "Comprehensive documentation"; Score = 100; Desc = "Case notes include issue description, troubleshooting steps, root cause, resolution, and any follow-up details. Another agent could pick up this case without additional context." }
                    @{ Label = "Adequate documentation"; Score = 66; Desc = "Key information is present but some details are missing or could be more thorough." }
                    @{ Label = "Incomplete documentation"; Score = 33; Desc = "Significant gaps in case notes - missing resolution details, troubleshooting steps, or customer communication history." }
                    @{ Label = "No documentation"; Score = 0; Desc = "Agent did not document the interaction in case notes." }
                )
            },
            @{
                Text         = "Were follow-up actions clearly defined and assigned?"
                Type         = $ChooseList
                Instructions = "If the resolution requires follow-up (e.g., replacement shipment, engineering review, customer callback, RMA processing), check that the next steps are documented with clear ownership and timelines."
                Options      = @(
                    @{ Label = "Follow-up documented and assigned"; Score = 100; Desc = "Next steps are documented with clear ownership, timeline, and expected outcome." }
                    @{ Label = "Follow-up needed but not documented"; Score = 0; Desc = "Additional actions are required but the agent did not document them or assign ownership." }
                    @{ Label = "No follow-up required"; Score = 50; Desc = "The case was fully resolved and no follow-up actions are needed." }
                )
            }
        )
    },

    # ===== Section 5: Communication & Professionalism =====
    @{
        Name        = "Communication & Professionalism"
        Description = "Evaluates the clarity, professionalism, and customer-centricity of the agent's communication throughout the interaction."
        Weight      = 10
        Questions   = @(
            @{
                Text         = "Was the agent's communication clear and professional?"
                Type         = $ChooseList
                Instructions = "Evaluate the overall quality of the agent's written or verbal communication. Consider grammar, tone, clarity of explanations, and appropriate use of technical language for the audience."
                Options      = @(
                    @{ Label = "Excellent"; Score = 100; Desc = "Communication was clear, professional, and polished. Technical concepts were explained appropriately for the audience." }
                    @{ Label = "Good"; Score = 66; Desc = "Professional communication with minor issues (e.g., small grammar errors, slightly unclear phrasing)." }
                    @{ Label = "Needs improvement"; Score = 33; Desc = "Communication was unclear, overly technical for the audience, or lacked professionalism." }
                    @{ Label = "Poor"; Score = 0; Desc = "Communication quality was a significant issue - confusing, rude, or unprofessional." }
                )
            },
            @{
                Text         = "Did the agent demonstrate empathy and active listening?"
                Type         = $YesNo
                Instructions = "Check if the agent acknowledged the customer's frustration or concern, paraphrased the issue to confirm understanding, and showed genuine interest in helping. Look for phrases that demonstrate empathy such as 'I understand your concern' or 'Let me make sure I have this right'."
                Options      = @(
                    @{ Label = "Yes"; Score = 100; Desc = "Agent demonstrated empathy, acknowledged the customer's situation, and confirmed understanding before proceeding." }
                    @{ Label = "No"; Score = 0; Desc = "Agent was transactional - no evidence of empathy, acknowledgment, or active listening." }
                )
            },
            @{
                Text         = "Did the agent summarize and set expectations before closing?"
                Type         = $YesNo
                Instructions = "Before ending the interaction, the agent should summarize what was discussed, what actions were taken, and what the customer can expect next (including timelines). Check for evidence of a clear closing summary."
                Options      = @(
                    @{ Label = "Yes"; Score = 100; Desc = "Agent summarized the interaction, confirmed the resolution or next steps, and set clear expectations." }
                    @{ Label = "No"; Score = 0; Desc = "Agent ended the interaction without summarizing or setting expectations." }
                )
            }
        )
    },

    # ===== Section 6: Tool Adoption & Efficiency =====
    @{
        Name        = "Tool Adoption & Efficiency"
        Description = "Evaluates the agent's use of available tools and AI capabilities to improve efficiency and service quality."
        Weight      = 10
        Questions   = @(
            @{
                Text         = "Did the agent leverage Copilot or AI assistance?"
                Type         = $ChooseList
                Instructions = "Check if the agent used Copilot features such as case summarization, suggested knowledge articles, draft responses, or sentiment analysis. Evaluate whether the AI assistance improved the interaction quality or efficiency."
                Options      = @(
                    @{ Label = "Used Copilot effectively"; Score = 100; Desc = "Agent used Copilot for summaries, KB suggestions, or drafts, and the AI assistance visibly improved quality or speed." }
                    @{ Label = "Used Copilot with limited benefit"; Score = 50; Desc = "Agent engaged Copilot features but the output was not meaningfully incorporated into the interaction." }
                    @{ Label = "Did not use available AI tools"; Score = 0; Desc = "No evidence that the agent used Copilot or AI assistance when it would have been beneficial." }
                    @{ Label = "Not applicable"; Score = 50; Desc = "The interaction was too brief or simple to warrant AI tool usage." }
                )
            },
            @{
                Text         = "Did the agent use the knowledge base search effectively?"
                Type         = $YesNo
                Instructions = "Check if the agent searched the knowledge base for relevant articles before providing a response. Evidence includes KB article references in case notes, linked articles, or documented search attempts."
                Options      = @(
                    @{ Label = "Yes"; Score = 100; Desc = "Agent searched the knowledge base and referenced or linked relevant articles." }
                    @{ Label = "No"; Score = 0; Desc = "No evidence that the agent consulted the knowledge base when it would have been appropriate." }
                )
            },
            @{
                Text         = "Was the overall interaction handled efficiently?"
                Type         = $ChooseList
                Instructions = "Consider the overall handling time relative to the issue complexity. An efficient interaction uses available tools, avoids unnecessary transfers, and reaches resolution without excessive back-and-forth."
                Options      = @(
                    @{ Label = "Highly efficient"; Score = 100; Desc = "Resolved quickly and appropriately using available tools. Minimal unnecessary steps." }
                    @{ Label = "Acceptable efficiency"; Score = 66; Desc = "Reasonable handling time for the complexity of the issue." }
                    @{ Label = "Below average"; Score = 0; Desc = "Unnecessary delays, rework, or excessive transfers. The interaction took longer than it should have." }
                    @{ Label = "Unable to assess"; Score = 50; Desc = "Insufficient data to evaluate efficiency (e.g., case still in progress)." }
                )
            }
        )
    }
)

# ============================================================
# STEP 1: Create Evaluation Criteria (Draft)
# ============================================================
Write-Host "`n--- Step 1: Create Evaluation Criteria ---" -ForegroundColor Yellow

$criteriaId = Find-OrCreate-Record `
    -EntitySet "msdyn_evaluationcriterias" `
    -Filter "msdyn_name eq '$(Escape-OData $CriteriaName)'" `
    -IdField "msdyn_evaluationcriteriaid" `
    -Body @{
    msdyn_name              = $CriteriaName
    msdyn_description       = $CriteriaDescription
    msdyn_numberofquestions = 21
    msdyn_languagecode      = "en-US"
} `
    -DisplayName $CriteriaName

if (-not $criteriaId) { throw "Failed to create evaluation criteria." }
Write-Host "  Criteria ID: $criteriaId" -ForegroundColor Cyan

# ============================================================
# STEP 2: Create Sections (Categories) & Questions
# ============================================================
Write-Host "`n--- Step 2: Create Sections & Questions ---" -ForegroundColor Yellow

# Collect category/question IDs for the criteriajson
$criteriaJsonSections = @()

$sectionIndex = 0
foreach ($section in $Sections) {
    $sectionIndex++
    Write-Host "`n  Section $sectionIndex : $($section.Name)" -ForegroundColor White

    $catId = Find-OrCreate-Record `
        -EntitySet "msdyn_evaluationcategories" `
        -Filter "msdyn_name eq '$(Escape-OData $section.Name)' and _msdyn_evaluationcriteria_value eq '$criteriaId'" `
        -IdField "msdyn_evaluationcategoryid" `
        -Body @{
        msdyn_name                            = $section.Name
        msdyn_description                     = $section.Description
        "msdyn_EvaluationCriteria@odata.bind" = "/msdyn_evaluationcriterias($criteriaId)"
    } `
        -DisplayName $section.Name

    if (-not $catId) { Write-Warning "Failed to create category: $($section.Name)"; continue }

    $questionIds = @()

    $qIndex = 0
    foreach ($q in $section.Questions) {
        $qIndex++

        # Build optionsjson -- each answer gets fresh GUIDs
        $optionsArray = @()
        $optIndex = 0
        foreach ($opt in $q.Options) {
            $optionsArray += @{
                value               = $optIndex
                answerId            = [guid]::NewGuid().ToString()
                answerLabel         = $opt.Label
                answerLabelId       = [guid]::NewGuid().ToString()
                answerDescription   = if ($opt.Desc) { $opt.Desc } else { "" }
                answerDescriptionId = ""
                score               = $opt.Score
            }
            $optIndex++
        }
        $optionsJson = $optionsArray | ConvertTo-Json -Depth 5 -Compress
        # Ensure it's always an array (single-element wraps as object)
        if ($optionsArray.Count -eq 1) { $optionsJson = "[$optionsJson]" }

        $escapedText = Escape-OData $q.Text
        $qId = Find-OrCreate-Record `
            -EntitySet "msdyn_evaluationquestions" `
            -Filter "msdyn_text eq '$escapedText' and _msdyn_evaluationcriteria_value eq '$criteriaId'" `
            -IdField "msdyn_evaluationquestionid" `
            -Body @{
            msdyn_text                            = $q.Text
            msdyn_questiontype                    = $q.Type
            msdyn_isairesponseenabled             = $true
            msdyn_required                        = $true
            msdyn_optionsjson                     = $optionsJson
            msdyn_questioninstructions            = $q.Instructions
            "msdyn_EvaluationCriteria@odata.bind" = "/msdyn_evaluationcriterias($criteriaId)"
            "msdyn_EvaluationCategory@odata.bind" = "/msdyn_evaluationcategories($catId)"
        } `
            -DisplayName "  Q$qIndex : $($q.Text.Substring(0, [Math]::Min(60, $q.Text.Length)))..."

        if ($qId) {
            $questionIds += $qId.ToString()
        } else {
            Write-Warning "Failed to create question: $($q.Text)"
        }
    }

    # Collect section data for criteriajson
    $criteriaJsonSections += @{
        type      = "category"
        id        = $catId.ToString()
        weight    = $section.Weight
        questions = @($questionIds | ForEach-Object { @{ id = $_ } })
    }

    Write-Host "    Created $($questionIds.Count) questions in this section" -ForegroundColor DarkGray
}

# ============================================================
# STEP 3: Create Criteria Version
# ============================================================
Write-Host "`n--- Step 3: Create Criteria Version ---" -ForegroundColor Yellow

# Build the criteriajson in the discovered format: [{"criteria":[...]}]
$criteriaJsonObj = @( @{ criteria = $criteriaJsonSections } )
$criteriaJsonStr = $criteriaJsonObj | ConvertTo-Json -Depth 10 -Compress

Write-Host "  CriteriaJSON length: $($criteriaJsonStr.Length) chars" -ForegroundColor DarkGray

$versionId = Find-OrCreate-Record `
    -EntitySet "msdyn_evaluationcriteriaversions" `
    -Filter "_msdyn_evaluationcriteria_value eq '$criteriaId' and msdyn_versionnumber eq 1" `
    -IdField "msdyn_evaluationcriteriaversionid" `
    -Body @{
    msdyn_name                            = "$CriteriaName - Version 1"
    msdyn_versionnumber                   = 1
    msdyn_scoringenabled                  = $true
    msdyn_criteriajson                    = $criteriaJsonStr
    msdyn_criteriainstructions            = $FormInstructions
    msdyn_useparentcriteriainstruction    = $false
    "msdyn_EvaluationCriteria@odata.bind" = "/msdyn_evaluationcriterias($criteriaId)"
} `
    -DisplayName "Criteria Version 1"

if (-not $versionId) { throw "Failed to create criteria version." }
Write-Host "  Version ID: $versionId" -ForegroundColor Cyan

# ============================================================
# STEP 4: Link Active Version & Publish
# ============================================================
Write-Host "`n--- Step 4: Link Active Version & Publish ---" -ForegroundColor Yellow

# Set the active version on the criteria record
Write-Host "  Setting active version on criteria..." -ForegroundColor White
$linkResult = Invoke-DataversePatch -EntitySet "msdyn_evaluationcriterias" -RecordId $criteriaId -Body @{
    "msdyn_ActiveVersion@odata.bind" = "/msdyn_evaluationcriteriaversions($versionId)"
}
if ($linkResult) { Write-Host "  Active version linked." -ForegroundColor Green }
else { Write-Warning "  Failed to set active version." }

# Publish the criteria (statuscode = 700610001 = Published)
# NOTE: Publishing criteria internally publishes the active version.
# Do NOT publish the version separately first -- that causes "No draft criteria version found" error.
Write-Host "  Publishing criteria..." -ForegroundColor White
$pubCriteria = Invoke-DataversePatch -EntitySet "msdyn_evaluationcriterias" -RecordId $criteriaId -Body @{
    statuscode = 700610001
    statecode  = 0
}
if ($pubCriteria) { Write-Host "  Criteria published." -ForegroundColor Green }
else { Write-Warning "  Failed to publish criteria. May need to publish via UI." }

# ============================================================
# STEP 5: Get Admin User for Plan Assignment
# ============================================================
Write-Host "`n--- Step 5: Get Admin User ---" -ForegroundColor Yellow

$adminUsers = Invoke-DataverseGet -EntitySet "systemusers" `
    -Filter "internalemailaddress eq 'admin@D365DemoTSCE30330346.onmicrosoft.com'" `
    -Select "systemuserid,fullname" -Top 1

if ($adminUsers -and $adminUsers.Count -gt 0) {
    $adminUserId = $adminUsers[0].systemuserid
    Write-Host "  Admin user: $($adminUsers[0].fullname) ($adminUserId)" -ForegroundColor Cyan
} else {
    Write-Warning "  Could not find admin user. Trying first admin..."
    $adminUsers = Invoke-DataverseGet -EntitySet "systemusers" `
        -Filter "accessmode eq 0" `
        -Select "systemuserid,fullname" -Top 1
    if ($adminUsers -and $adminUsers.Count -gt 0) {
        $adminUserId = $adminUsers[0].systemuserid
        Write-Host "  Using user: $($adminUsers[0].fullname) ($adminUserId)" -ForegroundColor Cyan
    } else {
        Write-Warning "  No admin user found. Plans will be created without assignee."
        $adminUserId = $null
    }
}

# ============================================================
# STEP 6: Create Evaluation Plans
# ============================================================
Write-Host "`n--- Step 6: Create Evaluation Plans ---" -ForegroundColor Yellow

$today = (Get-Date).AddDays(1).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$sixMonths = (Get-Date).AddMonths(6).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$dueDate = (Get-Date).AddDays(3).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Plan 1: Daily Case Quality Review
$plan1Body = @{
    msdyn_planname                        = "Daily Case Quality Review"
    msdyn_description                     = "Evaluates all resolved cases on a daily cadence using AI agent scoring against the Manufacturing Service Quality Standard."
    msdyn_evaluationmethod                = 700610001   # AI agent
    msdyn_frequency                       = 1           # Recurring
    msdyn_occurrence                      = 0           # Daily
    msdyn_recordtype                      = 0           # Case
    msdyn_planstartdate                   = $today
    msdyn_planenddate                     = $sixMonths
    msdyn_duedate                         = $dueDate
    msdyn_uniquename                      = "mfg_daily_case_review"
    "msdyn_EvaluationCriteria@odata.bind" = "/msdyn_evaluationcriterias($criteriaId)"
}

$plan1Id = Find-OrCreate-Record `
    -EntitySet "msdyn_evaluationplans" `
    -Filter "msdyn_planname eq 'Daily Case Quality Review'" `
    -IdField "msdyn_evaluationplanid" `
    -Body $plan1Body `
    -DisplayName "Daily Case Quality Review"

if ($plan1Id) {
    Write-Host "  Plan 1 ID: $plan1Id" -ForegroundColor Cyan
    # AssignedTo is a polymorphic lookup -- must be set via separate PATCH (not in POST body)
    if ($adminUserId) {
        Invoke-DataversePatch -EntitySet "msdyn_evaluationplans" -RecordId $plan1Id -Body @{
            "msdyn_AssignedTo@odata.bind" = "/systemusers($adminUserId)"
        } | Out-Null
        Write-Host "  Plan 1 assigned to admin user." -ForegroundColor Green
    }
} else {
    Write-Warning "  Failed to create Plan 1."
}

# Plan 2: Conversation Quality Review
$plan2Body = @{
    msdyn_planname                        = "Conversation Quality Review"
    msdyn_description                     = "Evaluates closed conversations across all channels using AI agent scoring against the Manufacturing Service Quality Standard."
    msdyn_evaluationmethod                = 700610001   # AI agent
    msdyn_frequency                       = 2           # Trigger
    msdyn_event                           = 0           # Closed Conversation
    msdyn_recordtype                      = 1           # Conversation
    msdyn_planstartdate                   = $today
    msdyn_planenddate                     = $sixMonths
    msdyn_duedate                         = $dueDate
    msdyn_uniquename                      = "mfg_conversation_review"
    "msdyn_EvaluationCriteria@odata.bind" = "/msdyn_evaluationcriterias($criteriaId)"
}

$plan2Id = Find-OrCreate-Record `
    -EntitySet "msdyn_evaluationplans" `
    -Filter "msdyn_planname eq 'Conversation Quality Review'" `
    -IdField "msdyn_evaluationplanid" `
    -Body $plan2Body `
    -DisplayName "Conversation Quality Review"

if ($plan2Id) {
    Write-Host "  Plan 2 ID: $plan2Id" -ForegroundColor Cyan
    # AssignedTo is a polymorphic lookup -- must be set via separate PATCH (not in POST body)
    if ($adminUserId) {
        Invoke-DataversePatch -EntitySet "msdyn_evaluationplans" -RecordId $plan2Id -Body @{
            "msdyn_AssignedTo@odata.bind" = "/systemusers($adminUserId)"
        } | Out-Null
        Write-Host "  Plan 2 assigned to admin user." -ForegroundColor Green
    }
} else {
    Write-Warning "  Failed to create Plan 2."
}

# ============================================================
# STEP 7: Export IDs
# ============================================================
Write-Host "`n--- Step 7: Export IDs ---" -ForegroundColor Yellow

$customerDataDir = Join-Path (Split-Path $scriptDir -Parent) "customers\Zurn\data"
if (-not (Test-Path $customerDataDir)) { New-Item -ItemType Directory -Path $customerDataDir -Force | Out-Null }

$exportData = @{
    criteriaId   = $criteriaId.ToString()
    criteriaName = $CriteriaName
    versionId    = $versionId.ToString()
    sections     = @($criteriaJsonSections | ForEach-Object {
            @{
                categoryId = $_.id
                weight     = $_.weight
                questions  = @($_.questions | ForEach-Object { $_.id })
            }
        })
    plans        = @(
        @{ planId = if ($plan1Id) { $plan1Id.ToString() } else { $null }; name = "Daily Case Quality Review" }
        @{ planId = if ($plan2Id) { $plan2Id.ToString() } else { $null }; name = "Conversation Quality Review" }
    )
}

$exportPath = Join-Path $customerDataDir "qm-criteria-ids.json"
$exportData | ConvertTo-Json -Depth 10 | Set-Content -Path $exportPath -Encoding UTF8
Write-Host "  Exported IDs to: $exportPath" -ForegroundColor Green

# ============================================================
# Summary
# ============================================================
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host " QM Evaluation Criteria & Plans - COMPLETE" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host ""
Write-Host "  Criteria : $CriteriaName" -ForegroundColor White
Write-Host "  Sections : $($Sections.Count)" -ForegroundColor White
Write-Host "  Questions: 21" -ForegroundColor White
Write-Host "  Version  : 1 (scoring enabled)" -ForegroundColor White
Write-Host "  Plans    : 2 (Daily Case Review + Conversation Review)" -ForegroundColor White
Write-Host ""
Write-Host "  NEXT STEPS:" -ForegroundColor Yellow
Write-Host '  1. Verify criteria in Copilot Service workspace > Evaluation criteria' -ForegroundColor White
Write-Host '  2. Set plan conditions in the UI (Case Status = Resolved, etc.)' -ForegroundColor White
Write-Host '  3. Activate plans if not already active' -ForegroundColor White
Write-Host '  4. Run a simulation: Evaluation criteria > Create Simulation' -ForegroundColor White
Write-Host ""
