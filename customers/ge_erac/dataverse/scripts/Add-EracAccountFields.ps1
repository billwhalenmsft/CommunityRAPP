<#
.SYNOPSIS
    Phase C1.1 — Add 8 ERAC cedent profile fields to the Account entity.
#>
param(
    [string]$Org = "https://orgecbce8ef.crm.dynamics.com",
    [string]$SolutionUniqueName = "GEERACLiteCRM",
    [string]$Prefix = "erac"
)
$ErrorActionPreference="Stop"
$token=(az account get-access-token --resource $Org|ConvertFrom-Json).accessToken
$H=@{Authorization="Bearer $token";"Content-Type"="application/json; charset=utf-8";Accept="application/json";"OData-MaxVersion"="4.0";"OData-Version"="4.0";"MSCRM.SolutionUniqueName"=$SolutionUniqueName}

function Invoke-Dv {
  param([string]$Method,[string]$Path,[object]$Body=$null,[hashtable]$Extra=$null)
  $h=$H.Clone(); if($Extra){$Extra.GetEnumerator()|%{$h[$_.Key]=$_.Value}}
  if($Method -in @("POST","PUT","PATCH")){$h["Prefer"]="return=representation"}
  $p=@{Uri="$Org/api/data/v9.2/$Path";Method=$Method;Headers=$h;TimeoutSec=120;UseBasicParsing=$true}
  if($Body){$p.Body=($Body|ConvertTo-Json -Depth 30)}
  try { $r=Invoke-WebRequest @p; if($r.Content){return $r.Content|ConvertFrom-Json}; return @{ok=$true} }
  catch { $code=try{$_.Exception.Response.StatusCode.value__}catch{0}; $msg=try{$_.ErrorDetails.Message}catch{$_.Exception.Message}; if(-not $msg){$msg="(no detail)"}; Write-Warning "X $Method $Path -> $code : $($msg.Substring(0,[Math]::Min(500,$msg.Length)))"; return $null }
}

function New-AttrLabel($txt){ @{ LocalizedLabels=@(@{ Label=$txt; LanguageCode=1033 }); UserLocalizedLabel=@{ Label=$txt; LanguageCode=1033 } } }

Write-Host "=== ADD ERAC CEDENT PROFILE FIELDS ===" -ForegroundColor Cyan

$existing = (Invoke-Dv GET 'EntityDefinitions(LogicalName=''account'')/Attributes?$select=LogicalName').value
$existingNames = @{}; $existing | %{ $existingNames[$_.LogicalName] = $true }

function Add-Attr($logical, $body) {
  if ($existingNames.ContainsKey($logical)) { Write-Host "  ⏭ $logical exists — skipping"; return }
  $r = Invoke-Dv POST "EntityDefinitions(LogicalName='account')/Attributes" $body
  if ($r) { Write-Host "  ✓ Created $logical" -ForegroundColor Green }
}

# 1. AM Best Rating (text)
Add-Attr "${Prefix}_ambestrating" @{
  "@odata.type"="Microsoft.Dynamics.CRM.StringAttributeMetadata"
  AttributeType="String"; AttributeTypeName=@{Value="StringType"}; SchemaName="${Prefix}_AmBestRating"
  DisplayName=(New-AttrLabel "AM Best Rating"); Description=(New-AttrLabel "AM Best Financial Strength Rating, e.g. A+ (Superior)")
  RequiredLevel=@{Value="None"}; MaxLength=20; FormatName=@{Value="Text"}
}

# 2. Cedent Tier (option set)
Add-Attr "${Prefix}_cedenttier" @{
  "@odata.type"="Microsoft.Dynamics.CRM.PicklistAttributeMetadata"
  AttributeType="Picklist"; AttributeTypeName=@{Value="PicklistType"}; SchemaName="${Prefix}_CedentTier"
  DisplayName=(New-AttrLabel "Cedent Tier"); Description=(New-AttrLabel "Strategic tier of the cedent relationship")
  RequiredLevel=@{Value="None"}
  OptionSet=@{
    "@odata.type"="Microsoft.Dynamics.CRM.OptionSetMetadata"; OptionSetType="Picklist"; IsGlobal=$false; Name="${Prefix}_cedenttier_options"
    Options=@(
      @{Value=100000000; Label=(New-AttrLabel "Tier 1 — Strategic")},
      @{Value=100000001; Label=(New-AttrLabel "Tier 2 — Core")},
      @{Value=100000002; Label=(New-AttrLabel "Tier 3 — Standard")},
      @{Value=100000003; Label=(New-AttrLabel "Watchlist")}
    )
  }
}

# 3. Years as Partner (whole number)
Add-Attr "${Prefix}_yearsaspartner" @{
  "@odata.type"="Microsoft.Dynamics.CRM.IntegerAttributeMetadata"
  AttributeType="Integer"; AttributeTypeName=@{Value="IntegerType"}; SchemaName="${Prefix}_YearsAsPartner"
  DisplayName=(New-AttrLabel "Years as Partner"); RequiredLevel=@{Value="None"}; MinValue=0; MaxValue=200; Format="None"
}

# 4. Renewal Date
Add-Attr "${Prefix}_renewaldate" @{
  "@odata.type"="Microsoft.Dynamics.CRM.DateTimeAttributeMetadata"
  AttributeType="DateTime"; AttributeTypeName=@{Value="DateTimeType"}; SchemaName="${Prefix}_RenewalDate"
  DisplayName=(New-AttrLabel "Renewal Date"); RequiredLevel=@{Value="None"}; Format="DateOnly"; DateTimeBehavior=@{Value="DateOnly"}
}

# 5. Financial Signatory Flag (boolean)
Add-Attr "${Prefix}_financialsignatoryflag" @{
  "@odata.type"="Microsoft.Dynamics.CRM.BooleanAttributeMetadata"
  AttributeType="Boolean"; AttributeTypeName=@{Value="BooleanType"}; SchemaName="${Prefix}_FinancialSignatoryFlag"
  DisplayName=(New-AttrLabel "Financial Signatory Flag"); Description=(New-AttrLabel "Active risk flag on financial signatory")
  RequiredLevel=@{Value="None"}
  OptionSet=@{
    "@odata.type"="Microsoft.Dynamics.CRM.BooleanOptionSetMetadata"; OptionSetType="Boolean"
    TrueOption=@{Value=1; Label=(New-AttrLabel "Active")}
    FalseOption=@{Value=0; Label=(New-AttrLabel "None")}
  }
  DefaultValue=$false
}

# 6. Gross Written Premium (money)
Add-Attr "${Prefix}_grosswrittenpremium" @{
  "@odata.type"="Microsoft.Dynamics.CRM.MoneyAttributeMetadata"
  AttributeType="Money"; AttributeTypeName=@{Value="MoneyType"}; SchemaName="${Prefix}_GrossWrittenPremium"
  DisplayName=(New-AttrLabel "Gross Written Premium"); RequiredLevel=@{Value="None"}; PrecisionSource=2
  MinValue=0; MaxValue=1000000000000
}

# 7. Lines of Business (multi-select picklist)
Add-Attr "${Prefix}_linesofbusiness" @{
  "@odata.type"="Microsoft.Dynamics.CRM.MultiSelectPicklistAttributeMetadata"
  AttributeType="Virtual"; AttributeTypeName=@{Value="MultiSelectPicklistType"}; SchemaName="${Prefix}_LinesOfBusiness"
  DisplayName=(New-AttrLabel "Lines of Business"); RequiredLevel=@{Value="None"}
  OptionSet=@{
    "@odata.type"="Microsoft.Dynamics.CRM.OptionSetMetadata"; OptionSetType="Picklist"; IsGlobal=$false; Name="${Prefix}_linesofbusiness_options"
    Options=@(
      @{Value=100000000; Label=(New-AttrLabel "Property")},
      @{Value=100000001; Label=(New-AttrLabel "Casualty")},
      @{Value=100000002; Label=(New-AttrLabel "Marine")},
      @{Value=100000003; Label=(New-AttrLabel "Aviation")},
      @{Value=100000004; Label=(New-AttrLabel "Life")},
      @{Value=100000005; Label=(New-AttrLabel "Health")},
      @{Value=100000006; Label=(New-AttrLabel "Cyber")},
      @{Value=100000007; Label=(New-AttrLabel "Specialty")}
    )
  }
}

# 8. Relationship Manager (lookup → systemuser)
$rmExists = $existingNames.ContainsKey("${Prefix}_relationshipmanagerid")
if (-not $rmExists) {
  $body = @{
    "@odata.type"="Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata"
    SchemaName="${Prefix}_systemuser_${Prefix}_relmgr_account"
    ReferencedEntity="systemuser"
    ReferencingEntity="account"
    Lookup=@{
      "@odata.type"="Microsoft.Dynamics.CRM.LookupAttributeMetadata"
      AttributeType="Lookup"; AttributeTypeName=@{Value="LookupType"}
      SchemaName="${Prefix}_RelationshipManagerId"
      DisplayName=(New-AttrLabel "Relationship Manager")
      Description=(New-AttrLabel "Internal RM owning the cedent relationship")
      RequiredLevel=@{Value="None"}
    }
    AssociatedMenuConfiguration=@{Behavior="UseCollectionName"; Group="Details"; Order=10000}
    CascadeConfiguration=@{Assign="NoCascade"; Delete="RemoveLink"; Merge="NoCascade"; Reparent="NoCascade"; Share="NoCascade"; Unshare="NoCascade"}
  }
  $r = Invoke-Dv POST "RelationshipDefinitions" $body
  if ($r) { Write-Host "  ✓ Created lookup ${Prefix}_relationshipmanagerid" -ForegroundColor Green }
} else { Write-Host "  ⏭ ${Prefix}_relationshipmanagerid exists — skipping" }

# Publish
Invoke-Dv POST "PublishXml" @{ParameterXml="<importexportxml><entities><entity>account</entity></entities></importexportxml>"} | Out-Null
Write-Host "`n✅ Field creation phase complete." -ForegroundColor Green
