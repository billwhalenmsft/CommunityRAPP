---
name: pp-solution-builder
description: Build, validate, and install Power Platform managed/unmanaged solution ZIPs from scratch. Covers solution.xml, customizations.xml, entity definitions, environment variables, Power Automate flows, Copilot Studio bot components, and PAC CLI deployment. Use this skill whenever creating a new Power Platform solution, packaging an existing one, troubleshooting import errors, or standardizing the deployment pipeline for any customer engagement.
applyTo: "customers/*/solution/**,skills/pp-solution-builder/**"
---

# Power Platform Solution Builder Skill

> Authoritative reference for building importable Power Platform solution ZIPs from source files.  
> Every rule here was learned by hitting the error in production — follow them and solutions import first time.

---

## Table of Contents

1. [Solution ZIP Structure](#1-solution-zip-structure)
2. [Content_Types.xml — The #1 Import Killer](#2-content_typesxml)
3. [solution.xml](#3-solutionxml)
4. [customizations.xml — Entity Definitions Must Be Inline](#4-customizationsxml)
5. [Dataverse Entities](#5-dataverse-entities)
6. [Environment Variables](#6-environment-variables)
7. [Power Automate Flows](#7-power-automate-flows)
8. [Copilot Studio Bot Components](#8-copilot-studio-bot-components)
9. [Build Script Pattern](#9-build-script-pattern)
10. [Import & Install Procedure](#10-import--install-procedure)
11. [PAC CLI Reference](#11-pac-cli-reference)
12. [Common Import Errors & Fixes](#12-common-import-errors--fixes)
13. [SAP / External System Demo Strategy](#13-sap--external-system-demo-strategy)

---

## 1. Solution ZIP Structure

A Power Platform solution ZIP is a flat package (no subdirectories are *required* at root level):

```
AscendProcurementAgent_1_0_0_0.zip
├── [Content_Types].xml          ← OPC manifest — MUST have correct namespace
├── solution.xml                 ← Solution manifest (unique name, version, publisher)
├── customizations.xml           ← ALL entity/component definitions INLINE here
├── EnvironmentVariables/
│   └── environmentvariables.xml
├── Workflows/
│   ├── FlowName_guid.json       ← Power Automate flow definitions
│   └── ...
├── BotComponents/
│   └── {publisher}_{BotName}/
│       ├── agent_manifest.json
│       └── Topics/
│           └── {schema}.yaml    ← Copilot Studio topic YAML
└── SampleData/
    └── entity_data.csv          ← Optional: sample/demo data CSVs
```

**Key rules:**
- `[Content_Types].xml`, `solution.xml`, and `customizations.xml` are always at root
- Entity definitions are INLINE in `customizations.xml` — never in separate `Entities/` subfolders
- The importer reads only these three root files plus registered component folders

---

## 2. `[Content_Types].xml`

> **Most common cause of import failure.** Missing namespace → "Required Types tag not found. Line 2, position 2"

### Correct template

```xml
<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="xml"  ContentType="application/xml"/>
  <Default Extension="json" ContentType="application/json"/>
  <Default Extension="yaml" ContentType="application/yaml"/>
  <Default Extension="csv"  ContentType="text/csv"/>
</Types>
```

### The rule
- Root element MUST be `<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">`
- Without the `xmlns` attribute: **import fails with cryptic error at line 2**
- Add a `<Default>` entry for every file extension you include in the ZIP

### Validation check (Python)
```python
import xml.etree.ElementTree as ET
OPC_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
root = ET.parse("[Content_Types].xml").getroot()
assert root.tag == f"{{{OPC_NS}}}Types", f"Missing OPC namespace! Got: {root.tag}"
```

---

## 3. `solution.xml`

Declares the solution identity and publisher. Power Platform enforces uniqueness on `UniqueName`.

```xml
<?xml version="1.0" encoding="utf-8"?>
<ImportExportXml version="9.2.24.10827"
  SolutionPackageVersion="9.2"
  languagecode="1033"
  generatedBy="CRMExport"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <SolutionManifest>
    <UniqueName>AscendProcurementAgent</UniqueName>
    <LocalizedNames>
      <LocalizedName description="Ascend Procurement Agent" languagecode="1033"/>
    </LocalizedNames>
    <Descriptions>
      <Description description="SAP ECC 6.0 Purchase Requisition Agent for Copilot Studio" languagecode="1033"/>
    </Descriptions>
    <Version>1.0.0.0</Version>
    <Managed>0</Managed>       <!-- 0 = unmanaged, 1 = managed -->
    <Publisher>
      <UniqueName>ascend</UniqueName>
      <LocalizedNames>
        <LocalizedName description="Ascend" languagecode="1033"/>
      </LocalizedNames>
      <EMailAddress/>
      <SupportingWebsiteUrl/>
      <CustomizationPrefix>ascend</CustomizationPrefix>
      <CustomizationOptionValuePrefix>100000</CustomizationOptionValuePrefix>
      <Addresses>
        <Address>
          <AddressNumber>1</AddressNumber>
          <AddressTypeCode>1</AddressTypeCode>
          <City/>
          <County/>
          <Country/>
          <Fax/>
          <FreightTermsCode/>
          <ImportSequenceNumber>0</ImportSequenceNumber>
          <Latitude>0</Latitude>
          <Longitude>0</Longitude>
          <Name>PrimaryAddress</Name>
          <PostalCode/>
          <PrimaryContactName/>
          <ShippingMethodCode>1</ShippingMethodCode>
          <StateOrProvince/>
          <Telephone1/>
          <Telephone2/>
          <Telephone3/>
          <TimeZoneRuleVersionNumber>0</TimeZoneRuleVersionNumber>
          <UPSZone/>
          <UTCOffset>0</UTCOffset>
          <WebSiteURL/>
        </Address>
      </Addresses>
    </Publisher>
    <RootComponents>
      <!-- List every top-level component type in the solution -->
      <RootComponent type="1" schemaName="ascend_sapvendor" behavior="0"/>
      <!-- type="1" = Entity, type="29" = Workflow/Flow, type="300" = Bot Component -->
    </RootComponents>
    <MissingDependencies/>
  </SolutionManifest>
</ImportExportXml>
```

**Publisher prefix rules:**
- `CustomizationPrefix` = short prefix for all schema names (e.g., `ascend_`)
- `CustomizationOptionValuePrefix` = starting value for picklist options (e.g., `100000`)
- All entity names, attribute names, and optionset values must use this prefix

**RootComponent type codes:**
| Type | Component |
|------|-----------|
| 1 | Entity |
| 2 | Attribute |
| 9 | OptionSet |
| 14 | Security Role |
| 29 | Workflow / Flow |
| 300 | Bot (Copilot Studio) |
| 301 | Bot Component (Topic) |
| 380 | CanvasApp |
| 9892 | Environment Variable Definition |

---

## 4. `customizations.xml` — Entity Definitions Must Be Inline

> **Second most common mistake:** Entity definitions in separate files are silently ignored during import.

### What NOT to do
```
solution_src/
  Entities/
    ascend_sapvendor/
      Entity.xml          ← IGNORED by importer. Only created by pac solution unpack.
```

### Correct structure

```xml
<?xml version="1.0" encoding="utf-8"?>
<ImportExportXml version="9.2.24.10827"
  SolutionPackageVersion="9.2"
  languagecode="1033"
  generatedBy="CRMExport"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

  <Entities>
    <!-- All entity definitions go INLINE here -->
    <Entity>...</Entity>
    <Entity>...</Entity>
  </Entities>

  <!-- These empty closing tags are REQUIRED. Missing any = import warning or error -->
  <Roles/>
  <FieldSecurityProfiles/>
  <Workflows/>
  <EntityMaps/>
  <EntityRelationships/>
  <OrganizationSettings/>
  <optionsets/>
  <CustomControls/>
  <EntityDataProviders/>
  <CanvasApps/>
  <Connectors/>

</ImportExportXml>
```

### Why separate files don't work
`pac solution unpack` splits `customizations.xml` into per-entity files for human readability and source control diffing. `pac solution pack` reassembles them. If you skip `pac solution pack` and ZIP the unpacked structure yourself, the importer only reads `customizations.xml` — all those separate XML files are never opened.

**Rule: either use `pac solution pack` to assemble the ZIP, or keep everything inline in `customizations.xml` yourself.**

---

## 5. Dataverse Entities

### Entity definition template

> **Critical:** Every `<entity>` element inside `<EntityInfo>` **must** include `PrimaryNameAttribute="fieldname"`.  
> Without it the import fails at 45% with error `0x80044355: PrimaryName attribute not found for Entity: <name>`.  
> All subsequent entities in the solution will show "Unprocessed" — nothing after the failing entity is imported.

```xml
<Entity>
  <Name>ascend_sapvendor</Name>
  <ObjectTypeCode>10200</ObjectTypeCode>       <!-- unique int, start at 10200 for custom -->
  <OriginalName>ascend_sapvendor</OriginalName>
  <OwnershipTypeMask>UserOwned</OwnershipTypeMask>  <!-- UserOwned or OrganizationOwned -->
  <EntityInfo>
    <!--                                              ↓ REQUIRED — must match an nvarchar Attribute Name below -->
    <entity Name="ascend_sapvendor" OwnershipType="UserOwned" CollectionName="ascend_sapvendors"
            PrimaryNameAttribute="ascend_name1">
      <LocalizedNames>
        <LocalizedName description="SAP Vendor" languagecode="1033"/>
      </LocalizedNames>
      <LocalizedCollectionNames>
        <LocalizedCollectionName description="SAP Vendors" languagecode="1033"/>
      </LocalizedCollectionNames>
      <LocalizedDescriptions>
        <LocalizedDescription description="Emulates SAP LFA1 vendor master. DEMO DATA ONLY." languagecode="1033"/>
      </LocalizedDescriptions>
    </entity>
  </EntityInfo>
  <Attributes>
    <!-- Primary key — required -->
    <Attribute PhysicalName="ascend_sapvendorid">
      <Type>primarykey</Type>
      <Name>ascend_sapvendorid</Name>
      <LogicalName>ascend_sapvendorid</LogicalName>
      <LocalizedNames><LocalizedName description="SAP Vendor Id" languagecode="1033"/></LocalizedNames>
    </Attribute>
    <!-- String field -->
    <Attribute PhysicalName="ascend_lifnr">
      <Type>nvarchar</Type>
      <Name>ascend_lifnr</Name>
      <LogicalName>ascend_lifnr</LogicalName>
      <MaxLength>12</MaxLength>
      <LocalizedNames><LocalizedName description="Vendor Number (LIFNR)" languagecode="1033"/></LocalizedNames>
    </Attribute>
    <!-- PRIMARY NAME field — must have IsPrimaryName + RequiredLevel, AND be referenced by PrimaryNameAttribute above -->
    <Attribute PhysicalName="ascend_name1">
      <Type>nvarchar</Type>
      <Name>ascend_name1</Name>
      <LogicalName>ascend_name1</LogicalName>
      <MaxLength>100</MaxLength>
      <IsPrimaryName>1</IsPrimaryName>
      <RequiredLevel>SystemRequired</RequiredLevel>
      <LocalizedNames><LocalizedName description="Vendor Name" languagecode="1033"/></LocalizedNames>
    </Attribute>
    <Attribute PhysicalName="ascend_status">
      <Type>picklist</Type>
      <Name>ascend_status</Name>
      <LogicalName>ascend_status</LogicalName>
      <LocalizedNames><LocalizedName description="Status" languagecode="1033"/></LocalizedNames>
    </Attribute>
  </Attributes>
  <optionsets>
    <optionset Name="ascend_status" localizedName="Vendor Status">
      <OptionSetType>picklist</OptionSetType>
      <options>
        <option value="100000"><labels><label description="Active" languagecode="1033"/></labels></option>
        <option value="100001"><labels><label description="Blocked" languagecode="1033"/></labels></option>
      </options>
    </optionset>
  </optionsets>
</Entity>
```

### Attribute type reference

| Type | Dataverse equivalent | Notes |
|------|---------------------|-------|
| `primarykey` | Unique Identifier | Always include; name = `{entity}id` |
| `nvarchar` | Text | Add `<MaxLength>` |
| `ntext` | Multiline Text | No MaxLength needed |
| `int` | Whole Number | |
| `decimal` | Decimal Number | |
| `money` | Currency | |
| `bit` | Yes/No (Boolean) | |
| `datetime` | Date and Time | |
| `picklist` | Choice (OptionSet) | Define options in `<optionsets>` |
| `lookup` | Lookup | Requires relationship definition |
| `owner` | Owner | For UserOwned entities |

### ObjectTypeCode rules
- Custom entities: use the range `10000`–`99999`
- Pick a base per engagement (e.g., `10200` for Ascend) and increment
- Must be unique across all entities in the solution

### PrimaryNameAttribute rules

Every entity requires **two things** for the primary name field — missing either causes `0x80044355`:

**1. `PrimaryNameAttribute` on the `<entity>` element:**
```xml
<entity Name="my_entity" OwnershipType="UserOwned" CollectionName="my_entities"
        PrimaryNameAttribute="my_displayname">
```

**2. `<IsPrimaryName>` and `<RequiredLevel>` inside the attribute itself:**
```xml
<Attribute PhysicalName="my_displayname">
  <Type>nvarchar</Type>
  <Name>my_displayname</Name>
  <LogicalName>my_displayname</LogicalName>
  <MaxLength>100</MaxLength>
  <IsPrimaryName>1</IsPrimaryName>
  <RequiredLevel>SystemRequired</RequiredLevel>
  <LocalizedNames><LocalizedName description="Display Name" languagecode="1033"/></LocalizedNames>
</Attribute>
```

Rules:
- Both the pointer on `<entity>` AND the flags on the `<Attribute>` are required — one without the other causes `0x80044355`
- The referenced attribute must be type `nvarchar`
- Cascade failure: the first entity with this error stops processing of ALL remaining entities

**PrimaryNameAttribute quick-pick guide by entity pattern:**

| Entity pattern | Best candidate | Reason |
|----------------|---------------|--------|
| Vendor / Person | Name field (e.g., `ascend_name1`) | Human-readable label |
| Purchase Requisition / Document | Short text / description (e.g., `ascend_txz01`) | Line item description |
| Account Assignment / Link record | Parent document number (e.g., `ascend_banfn`) | Best available identifier |
| Reference / Lookup table | Description field (e.g., `ascend_wgbez`, `ascend_ktext`) | What users see in dropdowns |
| Contract / Agreement | Contract number (e.g., `ascend_ebeln`) | Primary identifier |
| Approval / Strategy | Approver name (e.g., `ascend_approvername`) | Human-readable label |

### Picklist option value rules
- Values must start with your publisher's `CustomizationOptionValuePrefix`
- If prefix is `100000`, first option = `100000`, next = `100001`, etc.
- Do NOT use `1`, `2`, `3` or values from another publisher's range

---

## 6. Environment Variables

Store in `EnvironmentVariables/environmentvariables.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<environmentvariables>
  <environmentvariabledefinition>
    <SchemaName>ascend_DemoMode</SchemaName>
    <DisplayName>Demo Mode</DisplayName>
    <Description>Set to true for demo (Dataverse data), false for production (live SAP ERP connector).</Description>
    <ParameterKey>ascend_DemoMode</ParameterKey>
    <Type>Boolean</Type>
    <DefaultValue>true</DefaultValue>
    <IsRequired>false</IsRequired>
  </environmentvariabledefinition>

  <environmentvariabledefinition>
    <SchemaName>ascend_SAPEndpoint</SchemaName>
    <DisplayName>SAP ERP Endpoint</DisplayName>
    <Description>SAP ERP connector endpoint URL. Only used when DemoMode = false.</Description>
    <ParameterKey>ascend_SAPEndpoint</ParameterKey>
    <Type>String</Type>
    <DefaultValue>https://your-sap-endpoint</DefaultValue>
    <IsRequired>false</IsRequired>
  </environmentvariabledefinition>
</environmentvariables>
```

**Type values:** `String`, `Number`, `Boolean`, `JSON`, `DataSource`, `Secret`

**After import:** Set actual values in  
`make.powerapps.com → Solutions → [solution] → Environment Variables`

---

## 7. Power Automate Flows

Flow JSON stubs go in `Workflows/`. Format is Cloud Flow JSON:

```json
{
  "id": "/providers/Microsoft.ProcessSimple/environments/@{encodeURIComponent(variables('EnvironmentId'))}/flows/00000000-0000-0000-0000-000000000001",
  "name": "00000000-0000-0000-0000-000000000001",
  "type": "Microsoft.ProcessSimple/environments/flows",
  "properties": {
    "apiId": "/providers/Microsoft.PowerApps/apis/shared_logicflows",
    "displayName": "SAP: Create Purchase Requisition",
    "description": "DEMO: Emulates BAPI_PR_CREATE. In production, replace Dataverse actions with SAP ERP connector BAPI call.",
    "definition": {
      "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
      "contentVersion": "1.0.0.0",
      "triggers": {
        "manual": {
          "type": "Request",
          "kind": "PowerAppV2",
          "inputs": { "schema": { "type": "object", "properties": {} } }
        }
      },
      "actions": {
        "DemoModeCheck": {
          "type": "Compose",
          "inputs": "DEMO MODE: This action emulates SAP BAPI_PR_CREATE by writing to ascend_sappurchaserequisition Dataverse table. Production: replace with SAP ERP connector BAPI call.",
          "runAfter": {}
        }
      }
    },
    "state": "Started"
  }
}
```

**Tips:**
- Use a consistent GUID per flow — generate once and lock it in
- Always add a `DemoModeCheck` compose step describing which SAP BAPI/table is emulated
- Use `description` to document the production upgrade path

---

## 8. Copilot Studio Bot Components

Topics live in `BotComponents/{publisher}_{BotName}/Topics/`:

```
BotComponents/
  ascend_ProcurementAssistant/
    agent_manifest.json
    instructions.md
    Topics/
      ascend_topic_CreatePurchaseRequisition.yaml
      ascend_topic_CheckPRStatus.yaml
```

**agent_manifest.json** — minimal example:
```json
{
  "schemaName": "ascend_ProcurementAssistant",
  "displayName": "Procurement Assistant",
  "description": "SAP ECC 6.0 Purchase Requisition agent for Ascend.",
  "publisher": "ascend",
  "version": "1.0.0"
}
```

**instructions.md** — the system prompt / custom instructions for the agent.

**Topic YAML** — Copilot Studio `.mcs.yml` format:
```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    triggerQueries:
      - Create a purchase requisition
      - I need to order something
  actions:
    - kind: SendMessage
      id: greeting
      message: "I'll help you create a purchase requisition. What do you need to purchase?"
```

**Important caveat:** Topics created via solution import may not render in the Copilot Studio UI canvas on first import. If this happens:
1. Open the agent in Copilot Studio
2. Go to Topics → open any topic
3. Use Code Editor (YAML view) to paste the topic content manually
4. This is a known platform limitation — see `skills/power-platform/SKILL.md` for API workarounds

---

## 9. Build Script Pattern

Use a Python build script with an integrated validator. Reference implementation:  
`customers/ascend/solution/build_solution.py` — supports `--validate-only` flag.

### Minimal validator checklist (implement before every ZIP build)

```python
import xml.etree.ElementTree as ET, sys, zipfile
from pathlib import Path

OPC_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
errors = []

# 1. [Content_Types].xml namespace
root = ET.parse("solution_src/[Content_Types].xml").getroot()
if root.tag != f"{{{OPC_NS}}}Types":
    errors.append("[Content_Types].xml missing OPC namespace")

# 2. customizations.xml root + inline entities + PrimaryNameAttribute
root = ET.parse("solution_src/customizations.xml").getroot()
if root.tag != "ImportExportXml":
    errors.append("customizations.xml root must be <ImportExportXml>")
entities = root.find("Entities")
if entities is None or len(list(entities)) == 0:
    errors.append("customizations.xml: <Entities> empty — definitions must be inline")
else:
    for entity_elem in entities.findall("Entity"):
        name = entity_elem.findtext("Name", "unknown")
        ei = entity_elem.find("EntityInfo/entity")
        if ei is None:
            errors.append(f"Entity '{name}': missing <EntityInfo><entity> element")
            continue
        pna = ei.get("PrimaryNameAttribute")
        if not pna:
            errors.append(f"Entity '{name}': missing PrimaryNameAttribute (error 0x80044355 at import)")
        else:
            attr_names = [a.get("PhysicalName") for a in entity_elem.findall("Attributes/Attribute")]
            if pna not in attr_names:
                errors.append(f"Entity '{name}': PrimaryNameAttribute='{pna}' not in <Attributes>. Have: {attr_names}")
            else:
                # Also verify IsPrimaryName flag is set on the attribute itself
                for a in entity_elem.findall("Attributes/Attribute"):
                    if a.get("PhysicalName") == pna:
                        if a.find("IsPrimaryName") is None:
                            errors.append(f"Entity '{name}': attribute '{pna}' missing <IsPrimaryName>1</IsPrimaryName> (error 0x80044355)")
                        break

# 3. solution.xml required fields
root = ET.parse("solution_src/solution.xml").getroot()
for req in ["SolutionManifest/UniqueName", "SolutionManifest/Version", "SolutionManifest/Managed"]:
    if root.find(req) is None:
        errors.append(f"solution.xml missing <{req.split('/')[-1]}>")

if errors:
    for e in errors: print(f"ERROR: {e}")
    sys.exit(1)
print("Validation passed")
```

### Build steps

```python
import zipfile
from pathlib import Path

def build(output_zip, solution_src, **component_dirs):
    # 1. Validate (always first)
    run_validator(solution_src)

    # 2. Package
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in ["solution.xml", "customizations.xml", "[Content_Types].xml"]:
            zf.write(solution_src / f, f)
        for folder, arc_prefix in component_dirs.items():
            for src in Path(folder).rglob("*"):
                if src.is_file():
                    zf.write(src, f"{arc_prefix}/{src.relative_to(folder)}")

    # 3. Verify
    with zipfile.ZipFile(output_zip) as zf:
        names = zf.namelist()
    assert "solution.xml" in names and "customizations.xml" in names
    print(f"Built: {output_zip} ({output_zip.stat().st_size//1024} KB, {len(names)} files)")
```

---

## 10. Import & Install Procedure

### Standard import (UI)

1. Go to `https://make.powerapps.com`
2. Select your target environment (top-right dropdown)
3. Left nav → **Solutions** → **Import solution**
4. Upload ZIP → **Next**
5. Review connections (create new ones if prompted) → **Import**
6. Wait for "Solution imported successfully"

### Post-import steps

```
1. Set environment variables
   Solutions → [your solution] → Environment Variables
   → Set current value for each variable

2. Load sample data (if included)
   Dataverse → Tables → [entity] → Import data → Upload CSV
   Match column headers to field schema names

3. Activate flows
   Solutions → [your solution] → Cloud Flows
   → Turn on each flow (they import as Off by default)
   → Edit connection references to use your connectors

4. Configure Copilot Studio agent
   Solutions → [your solution] → Chatbots
   → Open agent → Topics → verify topics loaded
   → Publish the agent

5. Add agent to Teams channel (if applicable)
   Copilot Studio → Channels → Microsoft Teams → Turn on
```

### Import via PAC CLI

```bash
# Authenticate
pac auth create --url https://your-org.crm.dynamics.com

# Import unmanaged
pac solution import --path AscendProcurementAgent_1_0_0_0.zip --activate-plugins

# Import managed (cannot edit after import)
pac solution import --path AscendProcurementAgent_1_0_0_0.zip --activate-plugins --force-overwrite

# Check import status
pac solution list
```

### Validate before import (PAC CLI)

```bash
# Install PAC CLI if not present
npm install -g @microsoft/powerplatform-cli

# Run solution checker (uploads to tenant for analysis)
pac solution check --path AscendProcurementAgent_1_0_0_0.zip
```

---

## 11. PAC CLI Reference

| Command | Purpose |
|---------|---------|
| `pac auth create --url {org}` | Authenticate to environment |
| `pac auth list` | Show authenticated profiles |
| `pac auth select --index N` | Switch active environment |
| `pac solution list` | List solutions in current env |
| `pac solution import --path {zip}` | Import solution |
| `pac solution export --name {name} --path out.zip` | Export solution |
| `pac solution unpack --zipfile {zip} --folder {dir}` | Unpack for source control |
| `pac solution pack --zipfile {zip} --folder {dir}` | Pack from source back to ZIP |
| `pac solution check --path {zip}` | Validate before import |
| `pac solution version --strategy {patch\|minor\|major}` | Bump version |
| `pac copilot list` | List all copilots |
| `pac copilot publish --bot {guid}` | Publish a copilot |

### `pac solution unpack` / `pack` workflow (recommended for source control)

```bash
# Export from environment → unpack → commit to git
pac solution export --name AscendProcurementAgent --path raw.zip
pac solution unpack --zipfile raw.zip --folder solution_src

# After making changes → pack → import
pac solution pack --zipfile rebuilt.zip --folder solution_src
pac solution import --path rebuilt.zip
```

This is the safest workflow. `pack` handles assembling `customizations.xml` from the individual entity files, so you never need to hand-edit the inline XML.

---

## 12. Common Import Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Required Types tag not found. Line 2, position 2` | `[Content_Types].xml` missing `xmlns="http://schemas.openxmlformats.org/package/2006/content-types"` on `<Types>` | Add namespace attribute |
| `PrimaryName attribute not found for Entity: <name>` (0x80044355) | `<entity>` element in `<EntityInfo>` is missing `PrimaryNameAttribute="fieldname"` attribute, **OR** the referenced attribute is missing `<IsPrimaryName>1</IsPrimaryName>` inside its `<Attribute>` block | (1) Add `PrimaryNameAttribute="fieldname"` to the `<entity>` element. (2) Add `<IsPrimaryName>1</IsPrimaryName><RequiredLevel>SystemRequired</RequiredLevel>` inside that attribute's definition. Both are required. Stops entire import — all subsequent entities show "Unprocessed". |
| `The solution file is invalid` (generic) | Malformed XML in any root file | Run `xml.etree.ElementTree.parse()` on each file locally first |
| `Entity already exists` | Entity schema name conflict with existing solution | Rename entity or import as upgrade (bump version) |
| `A circular dependency was detected` | RootComponents reference components not included | Add missing components to `<RootComponents>` in solution.xml |
| `Publisher does not exist` | Publisher `UniqueName` in solution.xml not present in target env | Create publisher first, or use "Default Publisher" |
| `Entities not importing` | Entity definitions in `Entities/` subfolders, not inline | Move all `<Entity>` blocks into `customizations.xml` inline |
| `Option set values out of range` | Picklist values don't match publisher prefix | Change option values to match `CustomizationOptionValuePrefix` |
| `Connection reference not found` | Flow references a connector not configured in target | Create connection reference manually after import |
| `Topics not showing in Copilot Studio` | Topics created via solution import (platform limitation) | Paste topic YAML manually via Code Editor in Copilot Studio UI |
| `Solution import stuck at X%` | Large solution with many entities/flows | Wait — can take 10+ minutes. Check import status in Solutions list |

---

## 13. SAP / External System Demo Strategy

When building solutions that emulate SAP or other backend systems for demo purposes:

### Single toggle pattern

```xml
<!-- environmentvariables.xml -->
<environmentvariabledefinition>
  <SchemaName>ascend_DemoMode</SchemaName>
  <Type>Boolean</Type>
  <DefaultValue>true</DefaultValue>
  <Description>true = use Dataverse demo data; false = use live SAP ERP connector</Description>
</environmentvariabledefinition>
```

### Demo data labeling convention

Every Dataverse table that emulates an external system must include:
- `ascend_datasource` field (nvarchar 100) — value: `"SAP ECC 6.0 (Demo via Dataverse)"`
- `ascend_demodisclaimer` field (nvarchar 500) — value: `"Demo data only. Production reads from [TABLE] via [BAPI]."`

### Flow stub pattern

Every flow stub must have a `DemoModeCheck` compose step:
```json
"DemoModeCheck": {
  "type": "Compose",
  "inputs": "DEMO: Emulates SAP BAPI_PR_CREATE (table EBAN). Production: replace with SAP ERP connector BAPI call using environment variable ascend_SAPEndpoint.",
  "runAfter": {}
}
```

### SAP table → Dataverse entity mapping (Ascend reference)

| Dataverse Entity | SAP Table(s) | Description |
|-----------------|--------------|-------------|
| `ascend_sapvendor` | LFA1, LFB1, LFM1 | Vendor master |
| `ascend_sappurchaserequisition` | EBAN | PR item data |
| `ascend_sappraccountassignment` | EBKN | PR account assignment |
| `ascend_sapmaterialgroup` | T023, T023T | Material groups |
| `ascend_sapcostcenter` | CSKS | Cost centers |
| `ascend_sapglaccount` | SKA1, SKB1 | GL accounts |
| `ascend_sapcontract` | EKKO, EKPO, EORD | Contracts/outline agreements |
| `ascend_sapreleasestrategy` | T16FS, T161F | Release strategies (DoA) |

### Production upgrade path

When the customer is ready for live SAP:
1. Set `ascend_DemoMode` environment variable to `false`
2. In each flow: replace the `DemoModeCheck` compose + Dataverse list/create actions with the SAP ERP connector BAPI action
3. Configure SAP ERP connector with the customer's on-premise data gateway
4. Test each flow end-to-end against the SAP sandbox environment
5. No agent YAML changes required — the agent calls the same Power Automate trigger regardless

---

## Quick Reference Checklist

Before every solution import, verify:

- [ ] `[Content_Types].xml` has `xmlns="http://schemas.openxmlformats.org/package/2006/content-types"` on `<Types>`
- [ ] `customizations.xml` root is `<ImportExportXml>`
- [ ] All entity definitions are inline inside `<Entities>` in `customizations.xml`
- [ ] Required empty closing tags present (`<Roles/>`, `<FieldSecurityProfiles/>`, etc.)
- [ ] All XML files are well-formed (no unclosed tags, no stray characters after root close)
- [ ] Picklist option values use publisher prefix range (e.g., `100000`, `100001`)
- [ ] Each entity has a unique `<ObjectTypeCode>`
- [ ] `solution.xml` has `<UniqueName>`, `<Version>`, `<Managed>` in `<SolutionManifest>`
- [ ] Environment variable types are valid (`String`, `Boolean`, `Number`, etc.)
- [ ] Run `build_solution.py --validate-only` (or equivalent) before packaging
- [ ] Test import into a **dev/sandbox environment first** — never import untested to production
