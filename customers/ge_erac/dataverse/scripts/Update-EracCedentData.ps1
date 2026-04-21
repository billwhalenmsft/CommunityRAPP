<#
.SYNOPSIS
    Phase C1.2 — Populate OOTB + custom ERAC fields on cedent accounts.
#>
param(
    [string]$Org = "https://orgecbce8ef.crm.dynamics.com",
    [string]$SolutionUniqueName = "GEERACLiteCRM"
)
$ErrorActionPreference="Stop"
Add-Type -AssemblyName System.Web
$token=(az account get-access-token --resource $Org|ConvertFrom-Json).accessToken
$H=@{Authorization="Bearer $token";"Content-Type"="application/json; charset=utf-8";Accept="application/json";"OData-MaxVersion"="4.0";"OData-Version"="4.0"}

function Invoke-Dv {
  param([string]$Method,[string]$Path,[object]$Body=$null)
  $h=$H.Clone(); if($Method -in @("POST","PUT","PATCH")){$h["Prefer"]="return=representation"}
  $p=@{Uri="$Org/api/data/v9.2/$Path";Method=$Method;Headers=$h;TimeoutSec=120;UseBasicParsing=$true}
  if($Body){$p.Body=($Body|ConvertTo-Json -Depth 30)}
  try { $r=Invoke-WebRequest @p; if($r.Content){return $r.Content|ConvertFrom-Json}; return @{ok=$true} }
  catch { $code=try{$_.Exception.Response.StatusCode.value__}catch{0}; $msg=try{$_.ErrorDetails.Message}catch{$_.Exception.Message}; if(-not $msg){$msg="(no detail)"}; Write-Warning "X $Method $Path -> $code : $($msg.Substring(0,[Math]::Min(500,$msg.Length)))"; return $null }
}

Write-Host "=== POPULATE CEDENT ACCOUNTS ===" -ForegroundColor Cyan

# Cedent profiles — keyed by name
$cedents = @{
  "Titan Mutual Re" = @{
    revenue = 4200000000; numberofemployees = 1850
    telephone1 = "+1 314 555 0142"; websiteurl = "https://www.titanmre.com"
    tickersymbol = "TMRE"; industrycode = 27  # Insurance
    address1_line1 = "777 Olive Street"; address1_city = "St. Louis"; address1_stateorprovince = "MO"; address1_postalcode = "63101"; address1_country = "USA"
    description = "Midwest-based mutual reinsurer specializing in property and casualty treaty business. Tier 1 strategic partner since 2008. Strong loss-cost discipline; active financial signatory risk flag opened Q4 2025 pending FCB review."
    erac_ambestrating = "A (Excellent)"; erac_cedenttier = 100000000  # Tier 1
    erac_yearsaspartner = 17; erac_renewaldate = "2026-09-30"
    erac_financialsignatoryflag = $true
    erac_grosswrittenpremium = 1240000000
    erac_linesofbusiness = "100000000,100000001,100000002"  # Property, Casualty, Marine
  }
  "Acme Reinsurance" = @{
    revenue = 7800000000; numberofemployees = 3200
    telephone1 = "+1 212 555 0188"; websiteurl = "https://www.acmere.com"
    tickersymbol = "ACRE"; industrycode = 27
    address1_line1 = "200 Park Avenue"; address1_city = "New York"; address1_stateorprovince = "NY"; address1_postalcode = "10166"; address1_country = "USA"
    description = "Global reinsurer with diversified property/casualty/specialty book. Tier 1 partner with $2.1B GWP. Excellent treaty performance through 2025; renewing Q1 2026."
    erac_ambestrating = "A+ (Superior)"; erac_cedenttier = 100000000
    erac_yearsaspartner = 22; erac_renewaldate = "2026-03-31"
    erac_financialsignatoryflag = $false; erac_grosswrittenpremium = 2100000000
    erac_linesofbusiness = "100000000,100000001,100000007"  # Property, Casualty, Specialty
  }
  "Meridian Re Partners" = @{
    revenue = 1900000000; numberofemployees = 620
    telephone1 = "+1 415 555 0163"; websiteurl = "https://www.meridianrep.com"
    tickersymbol = ""; industrycode = 27
    address1_line1 = "555 California Street"; address1_city = "San Francisco"; address1_stateorprovince = "CA"; address1_postalcode = "94104"; address1_country = "USA"
    description = "Boutique specialty reinsurer focused on cyber and professional liability. Tier 2 core partner; rapid growth in cyber book over 2024-25."
    erac_ambestrating = "A- (Excellent)"; erac_cedenttier = 100000001
    erac_yearsaspartner = 8; erac_renewaldate = "2026-06-30"
    erac_financialsignatoryflag = $false; erac_grosswrittenpremium = 480000000
    erac_linesofbusiness = "100000006,100000007"  # Cyber, Specialty
  }
  "Summit Life & Casualty" = @{
    revenue = 5100000000; numberofemployees = 2400
    telephone1 = "+1 303 555 0119"; websiteurl = "https://www.summitlc.com"
    tickersymbol = "SLAC"; industrycode = 27
    address1_line1 = "1801 California Street"; address1_city = "Denver"; address1_stateorprovince = "CO"; address1_postalcode = "80202"; address1_country = "USA"
    description = "Composite life and casualty reinsurer. Tier 2 core partner; reserve adequacy trending below threshold over last two periods — flagged for QBR review."
    erac_ambestrating = "B++ (Good)"; erac_cedenttier = 100000003  # Watchlist
    erac_yearsaspartner = 12; erac_renewaldate = "2026-12-31"
    erac_financialsignatoryflag = $true; erac_grosswrittenpremium = 890000000
    erac_linesofbusiness = "100000004,100000005,100000001"  # Life, Health, Casualty
  }
  "Pacific Coastal Re" = @{
    revenue = 2700000000; numberofemployees = 940
    telephone1 = "+1 206 555 0177"; websiteurl = "https://www.paccoastalre.com"
    tickersymbol = ""; industrycode = 27
    address1_line1 = "1201 Third Avenue"; address1_city = "Seattle"; address1_stateorprovince = "WA"; address1_postalcode = "98101"; address1_country = "USA"
    description = "West Coast property catastrophe reinsurer with significant CA/PNW earthquake exposure. Tier 2; strong rating and consistent partnership."
    erac_ambestrating = "A (Excellent)"; erac_cedenttier = 100000001
    erac_yearsaspartner = 15; erac_renewaldate = "2026-04-30"
    erac_financialsignatoryflag = $false; erac_grosswrittenpremium = 720000000
    erac_linesofbusiness = "100000000,100000003"  # Property, Aviation
  }
  "Harbor Group" = @{
    revenue = 1100000000; numberofemployees = 380
    telephone1 = "+1 617 555 0124"; websiteurl = "https://www.harborgrouprein.com"
    tickersymbol = ""; industrycode = 27
    address1_line1 = "100 Federal Street"; address1_city = "Boston"; address1_stateorprovince = "MA"; address1_postalcode = "02110"; address1_country = "USA"
    description = "New England regional reinsurer. Tier 3 standard partner; primarily property and marine treaty business in Northeast."
    erac_ambestrating = "A- (Excellent)"; erac_cedenttier = 100000002
    erac_yearsaspartner = 9; erac_renewaldate = "2026-08-31"
    erac_financialsignatoryflag = $false; erac_grosswrittenpremium = 310000000
    erac_linesofbusiness = "100000000,100000002"  # Property, Marine
  }
}

# Find each by name
foreach ($name in $cedents.Keys) {
  $esc = $name.Replace("'","''")
  $encName = [System.Web.HttpUtility]::UrlEncode($esc).Replace("+","%20")
  $r = Invoke-Dv GET "accounts?`$select=accountid,name&`$filter=name eq '$encName'"
  if (-not $r -or $r.value.Count -eq 0) { Write-Warning "  ⚠ '$name' not found"; continue }
  $accountId = $r.value[0].accountid
  $body = $cedents[$name].Clone()
  # Convert lines of business CSV → MultiSelect
  if ($body.ContainsKey("erac_linesofbusiness")) { $body.erac_linesofbusiness = $body.erac_linesofbusiness }
  $upd = Invoke-Dv PATCH "accounts($accountId)" $body
  if ($upd) { Write-Host "  ✓ $name" -ForegroundColor Green } else { Write-Warning "  ✗ $name failed" }
}

Write-Host "`n✅ Cedent population complete." -ForegroundColor Green
