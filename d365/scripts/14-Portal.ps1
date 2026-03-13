<#
.SYNOPSIS
    Customizes the Power Pages Customer Self-Service portal with Zurn Elkay branding.
.DESCRIPTION
    Discovers the portal structure in Dataverse and applies Zurn Elkay branding:
      - Custom CSS with brand colors
      - Branded header with logo and navigation
      - Branded footer with company info and links
      - Home page with hero, product category tiles, and quick actions
      - Omnichannel chat widget integration (optional)
.PARAMETER DiscoverOnly
    When set, only discovers and reports the portal structure without making changes.
.NOTES
    Prerequisites:
      - Power Pages site created (Customer Self-Service template)
      - az login completed
      - DataverseHelper.psm1 in the same directory
    Run with: .\14-Portal.ps1
    Discovery only: .\14-Portal.ps1 -DiscoverOnly
#>

param(
  [switch]$DiscoverOnly
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Connect-Dataverse

# ============================================================
# Step 1: Discovery - Find the Power Pages site
# ============================================================
Write-StepHeader "1" "Discovering Power Pages Site"

$websites = Invoke-DataverseGet -EntitySet "adx_websites" -Select "adx_websiteid,adx_name"
if (-not $websites -or $websites.Count -eq 0) {
  Write-Error "No Power Pages website found in Dataverse. Please create a portal site first."
  return
}

Write-Host "Found $($websites.Count) website(s):" -ForegroundColor Green
for ($i = 0; $i -lt $websites.Count; $i++) {
  $wName = $websites[$i].adx_name
  $wId = $websites[$i].adx_websiteid
  Write-Host "  [$i] $wName  ($wId)" -ForegroundColor White
}

# Target the Zurn Elkay Customer Care site specifically
$targetSiteId = "2dd891fe-1418-f111-8342-7c1e52143136"
$site = $websites | Where-Object { $_.adx_websiteid -eq $targetSiteId }
if (-not $site) {
  # Fallback: match by name fragment
  $site = $websites | Where-Object { $_.adx_name -like "*Zurn*" } | Select-Object -First 1
}
if (-not $site) {
  Write-Error "Could not find Zurn Elkay Customer Care site ($targetSiteId). Aborting."
  return
}
$siteId = $site.adx_websiteid
$siteName = $site.adx_name
Write-Host "`nUsing site: $siteName ($siteId)" -ForegroundColor Cyan

# --- Discover Web Templates ---
Write-Host "`n--- Web Templates ---" -ForegroundColor Yellow
$templates = Invoke-DataverseGet -EntitySet "adx_webtemplates" `
  -Filter "_adx_websiteid_value eq $siteId" `
  -Select "adx_webtemplateid,adx_name"
$templateMap = @{}
if ($templates -and $templates.Count -gt 0) {
  foreach ($t in $templates) {
    Write-Host "  $($t.adx_name)  [$($t.adx_webtemplateid)]"
    $templateMap[$t.adx_name] = $t
  }
  Write-Host "  Total: $($templates.Count)" -ForegroundColor DarkGray
} else {
  Write-Host "  (none found)" -ForegroundColor DarkGray
}

# --- Discover Web Pages ---
Write-Host "`n--- Web Pages ---" -ForegroundColor Yellow
$pages = Invoke-DataverseGet -EntitySet "adx_webpages" `
  -Filter "_adx_websiteid_value eq $siteId" `
  -Select "adx_webpageid,adx_name,adx_partialurl,adx_isroot,_adx_parentpageid_value"
$pageMap = @{}
if ($pages -and $pages.Count -gt 0) {
  foreach ($p in $pages) {
    $rootTag = ""
    if ($p.adx_isroot -eq $true) { $rootTag = " [ROOT]" }
    $parentTag = ""
    if ($p._adx_parentpageid_value) { $parentTag = " (parent: $($p._adx_parentpageid_value))" }
    Write-Host "  $($p.adx_name) | /$($p.adx_partialurl)$rootTag$parentTag  [$($p.adx_webpageid)]"
    $pageMap[$p.adx_name + $rootTag] = $p
  }
  Write-Host "  Total: $($pages.Count)" -ForegroundColor DarkGray
} else {
  Write-Host "  (none found)" -ForegroundColor DarkGray
}

# --- Discover Content Snippets ---
Write-Host "`n--- Content Snippets ---" -ForegroundColor Yellow
$snippets = Invoke-DataverseGet -EntitySet "adx_contentsnippets" `
  -Filter "_adx_websiteid_value eq $siteId" `
  -Select "adx_contentsnippetid,adx_name"
if ($snippets -and $snippets.Count -gt 0) {
  foreach ($s in $snippets) {
    Write-Host "  $($s.adx_name)  [$($s.adx_contentsnippetid)]"
  }
  Write-Host "  Total: $($snippets.Count)" -ForegroundColor DarkGray
} else {
  Write-Host "  (none found)" -ForegroundColor DarkGray
}

# --- Discover Site Settings ---
Write-Host "`n--- Site Settings (first 30) ---" -ForegroundColor Yellow
$settings = Invoke-DataverseGet -EntitySet "adx_sitesettings" `
  -Filter "_adx_websiteid_value eq $siteId" `
  -Select "adx_sitesettingid,adx_name,adx_value" `
  -Top 30
if ($settings -and $settings.Count -gt 0) {
  foreach ($s in $settings) {
    $val = $s.adx_value
    if ($val -and $val.Length -gt 60) { $val = $val.Substring(0, 60) + "..." }
    Write-Host "  $($s.adx_name) = $val"
  }
  Write-Host "  (showing up to 30)" -ForegroundColor DarkGray
} else {
  Write-Host "  (none found)" -ForegroundColor DarkGray
}

# --- Discover Page Templates ---
Write-Host "`n--- Page Templates ---" -ForegroundColor Yellow
$pageTemplates = Invoke-DataverseGet -EntitySet "adx_pagetemplates" `
  -Filter "_adx_websiteid_value eq $siteId" `
  -Select "adx_pagetemplateid,adx_name"
if ($pageTemplates -and $pageTemplates.Count -gt 0) {
  foreach ($pt in $pageTemplates) {
    Write-Host "  $($pt.adx_name)  [$($pt.adx_pagetemplateid)]"
  }
  Write-Host "  Total: $($pageTemplates.Count)" -ForegroundColor DarkGray
} else {
  Write-Host "  (none found)" -ForegroundColor DarkGray
}

# --- Discover Publishing States ---
Write-Host "`n--- Publishing States ---" -ForegroundColor Yellow
$pubStates = Invoke-DataverseGet -EntitySet "adx_publishingstates" `
  -Filter "_adx_websiteid_value eq $siteId" `
  -Select "adx_publishingstateid,adx_name"
if ($pubStates -and $pubStates.Count -gt 0) {
  foreach ($ps in $pubStates) {
    Write-Host "  $($ps.adx_name)  [$($ps.adx_publishingstateid)]"
  }
} else {
  Write-Host "  (none found)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host " Discovery Complete" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

if ($DiscoverOnly) {
  Write-Host "`nRun without -DiscoverOnly to apply branding." -ForegroundColor Yellow
  return
}

Write-Host ""
Write-Host "Proceeding with branding customization..." -ForegroundColor Green
Write-Host ""

# ============================================================
# Step 2: Update Header Web Template
# ============================================================
Write-StepHeader "2" "Applying Branded Header"

$headerTemplate = $null
foreach ($t in $templates) {
  if ($t.adx_name -eq "Header") {
    $headerTemplate = $t
    break
  }
}

if (-not $headerTemplate) {
  Write-Warning "No 'Header' web template found. Skipping header branding."
  Write-Host "  Available templates: $($templates | ForEach-Object { $_.adx_name } | Join-String -Separator ', ')"
} else {
  Write-Host "  Found Header template: $($headerTemplate.adx_webtemplateid)" -ForegroundColor Green

  # Branded header with embedded CSS for entire portal
  $headerSource = @'
<style>
/* ============================================================
   Zurn Elkay Water Solutions - Portal Brand Styles
   ============================================================ */
:root {
  --ze-navy: #002855;
  --ze-blue: #0072CE;
  --ze-teal: #00B5AD;
  --ze-gray-50: #F7FAFC;
  --ze-gray-100: #EDF2F7;
  --ze-gray-200: #E2E8F0;
  --ze-gray-600: #718096;
  --ze-gray-800: #2D3748;
  --ze-white: #FFFFFF;
}

/* --- Header --- */
.ze-header {
  background: var(--ze-navy);
  padding: 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  position: sticky;
  top: 0;
  z-index: 1000;
}
.ze-header-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
}
.ze-logo {
  display: flex;
  align-items: center;
  text-decoration: none;
  gap: 8px;
}
.ze-logo-text {
  font-family: 'Segoe UI', Arial, sans-serif;
  font-weight: 700;
  font-size: 22px;
  letter-spacing: 2.5px;
  color: var(--ze-white);
  text-transform: uppercase;
}
.ze-logo-elkay {
  font-weight: 300;
  margin-left: 1px;
}
.ze-logo-sub {
  font-size: 10px;
  letter-spacing: 1.5px;
  color: var(--ze-teal);
  text-transform: uppercase;
  font-weight: 400;
}
.ze-nav {
  display: flex;
  align-items: center;
  gap: 4px;
  list-style: none;
  margin: 0;
  padding: 0;
}
.ze-nav a {
  color: rgba(255,255,255,0.85);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  padding: 8px 14px;
  border-radius: 6px;
  transition: background 0.2s, color 0.2s;
}
.ze-nav a:hover,
.ze-nav a:focus {
  background: rgba(255,255,255,0.12);
  color: var(--ze-white);
}
.ze-nav .active a {
  background: rgba(255,255,255,0.15);
  color: var(--ze-white);
}
.ze-user-menu {
  display: flex;
  align-items: center;
  gap: 12px;
}
.ze-user-name {
  color: rgba(255,255,255,0.8);
  font-size: 13px;
}
.ze-user-btn {
  color: var(--ze-white);
  background: var(--ze-blue);
  border: none;
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  transition: background 0.2s;
  cursor: pointer;
}
.ze-user-btn:hover {
  background: #005FA3;
  color: var(--ze-white);
  text-decoration: none;
}

/* --- Hero Section --- */
.ze-hero {
  background: linear-gradient(135deg, var(--ze-navy) 0%, #003A75 50%, var(--ze-blue) 100%);
  color: var(--ze-white);
  text-align: center;
  padding: 64px 24px;
  margin: -20px -15px 40px -15px;
}
.ze-hero h1 {
  font-size: 36px;
  font-weight: 700;
  margin: 0 0 12px 0;
  color: var(--ze-white);
}
.ze-hero p {
  font-size: 18px;
  opacity: 0.9;
  margin: 0;
  font-weight: 300;
}

/* --- Product Category Tiles --- */
.ze-section-title {
  text-align: center;
  font-size: 28px;
  font-weight: 700;
  color: var(--ze-gray-800);
  margin: 0 0 32px 0;
}
.ze-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  max-width: 1000px;
  margin: 0 auto 48px auto;
  padding: 0 16px;
}
@media (max-width: 768px) {
  .ze-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 480px) {
  .ze-grid {
    grid-template-columns: 1fr;
  }
}
.ze-tile {
  background: var(--ze-white);
  border: 1px solid var(--ze-gray-200);
  border-radius: 12px;
  padding: 28px 20px;
  text-align: center;
  text-decoration: none;
  color: var(--ze-gray-800);
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.ze-tile:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0,40,85,0.12);
  border-color: var(--ze-blue);
  text-decoration: none;
  color: var(--ze-gray-800);
}
.ze-tile-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  color: var(--ze-white);
}
.ze-tile-icon svg {
  width: 32px;
  height: 32px;
}
.ze-tile-hydration .ze-tile-icon { background: #0077C8; }
.ze-tile-sinks .ze-tile-icon { background: #00B5AD; }
.ze-tile-flush .ze-tile-icon { background: #2C5282; }
.ze-tile-drainage .ze-tile-icon { background: #38A169; }
.ze-tile-backflow .ze-tile-icon { background: #805AD5; }
.ze-tile-filtration .ze-tile-icon { background: #DD6B20; }
.ze-tile h3 {
  font-size: 17px;
  font-weight: 700;
  margin: 0 0 6px 0;
}
.ze-tile p {
  font-size: 13px;
  color: var(--ze-gray-600);
  margin: 0;
  line-height: 1.4;
}

/* --- Quick Action Cards --- */
.ze-action-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  max-width: 1000px;
  margin: 0 auto 48px auto;
  padding: 0 16px;
}
@media (max-width: 768px) {
  .ze-action-grid {
    grid-template-columns: 1fr;
  }
}
.ze-action-card {
  background: var(--ze-gray-50);
  border: 2px solid var(--ze-gray-200);
  border-radius: 12px;
  padding: 28px 24px;
  text-align: center;
  text-decoration: none;
  color: var(--ze-gray-800);
  transition: border-color 0.2s, background 0.2s;
}
.ze-action-card:hover {
  border-color: var(--ze-blue);
  background: var(--ze-white);
  text-decoration: none;
  color: var(--ze-gray-800);
}
.ze-action-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 12px auto;
  color: var(--ze-blue);
}
.ze-action-icon svg {
  width: 48px;
  height: 48px;
}
.ze-action-card h3 {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: var(--ze-navy);
}
.ze-action-card p {
  font-size: 14px;
  color: var(--ze-gray-600);
  margin: 0;
}

/* --- Footer --- */
.ze-footer {
  background: var(--ze-navy);
  color: rgba(255,255,255,0.85);
  padding: 48px 24px 24px 24px;
  margin-top: 48px;
}
.ze-footer-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 40px;
}
@media (max-width: 768px) {
  .ze-footer-inner {
    grid-template-columns: 1fr;
    gap: 24px;
  }
}
.ze-footer h4 {
  color: var(--ze-white);
  font-size: 16px;
  font-weight: 700;
  margin: 0 0 12px 0;
}
.ze-footer p {
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 4px 0;
}
.ze-footer ul {
  list-style: none;
  margin: 0;
  padding: 0;
}
.ze-footer ul li {
  margin-bottom: 6px;
}
.ze-footer a {
  color: var(--ze-teal);
  text-decoration: none;
  font-size: 14px;
}
.ze-footer a:hover {
  color: var(--ze-white);
  text-decoration: underline;
}
.ze-footer-bottom {
  max-width: 1200px;
  margin: 24px auto 0 auto;
  padding-top: 20px;
  border-top: 1px solid rgba(255,255,255,0.15);
  text-align: center;
  font-size: 13px;
  color: rgba(255,255,255,0.5);
}

/* --- Global Overrides --- */
body {
  font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
  color: var(--ze-gray-800);
}
.navbar, .navbar-default, .navbar-static-top {
  display: none !important;
}
.page-heading {
  display: none;
}
#portal-footer, footer.portal-footer {
  display: none !important;
}
.container.body-content {
  padding-top: 0;
}
</style>

<header class="ze-header">
  <div class="ze-header-inner">
    <a href="~/" class="ze-logo">
      <div>
        <span class="ze-logo-text">ZURN<span class="ze-logo-elkay">ELKAY</span></span>
        <div class="ze-logo-sub">Support Center</div>
      </div>
    </a>
    <ul class="ze-nav">
      <li><a href="~/">Home</a></li>
      <li><a href="~/knowledgebase/">Knowledge Base</a></li>
      <li><a href="~/support/create-case/">Submit Request</a></li>
      <li><a href="~/support/">My Cases</a></li>
    </ul>
    <div class="ze-user-menu">
      {% if user %}
        <span class="ze-user-name">{{ user.fullname }}</span>
        <a href="{{ website.sign_out_url }}" class="ze-user-btn">Sign Out</a>
      {% else %}
        <a href="{{ website.sign_in_url }}" class="ze-user-btn">Sign In</a>
      {% endif %}
    </div>
  </div>
</header>
'@

  Write-Host "  Updating Header template..." -ForegroundColor Cyan
  $result = Invoke-DataversePatch `
    -EntitySet "adx_webtemplates" `
    -RecordId ([guid]$headerTemplate.adx_webtemplateid) `
    -Body @{ adx_source = $headerSource }
  if ($result) {
    Write-Host "  Header template updated successfully." -ForegroundColor Green
  } else {
    Write-Warning "  Failed to update Header template."
  }
}

# ============================================================
# Step 3: Update Footer Web Template
# ============================================================
Write-StepHeader "3" "Applying Branded Footer"

$footerTemplate = $null
foreach ($t in $templates) {
  if ($t.adx_name -eq "Footer") {
    $footerTemplate = $t
    break
  }
}

if (-not $footerTemplate) {
  Write-Warning "No 'Footer' web template found. Skipping footer branding."
} else {
  Write-Host "  Found Footer template: $($footerTemplate.adx_webtemplateid)" -ForegroundColor Green

  $footerSource = @'
<footer class="ze-footer">
  <div class="ze-footer-inner">
    <div>
      <h4>Zurn Elkay Water Solutions</h4>
      <p>511 W. Freshwater Way<br>Milwaukee, WI 53204</p>
      <p style="margin-top: 12px;">
        For over two centuries combined, the businesses of Zurn Elkay have been
        providing clean water solutions that promote health and safety.
      </p>
    </div>
    <div>
      <h4>Quick Links</h4>
      <ul>
        <li><a href="~/knowledgebase/">Knowledge Base</a></li>
        <li><a href="~/support/create-case/">Submit a Request</a></li>
        <li><a href="~/support/">Track My Cases</a></li>
        <li><a href="~/profile/">My Profile</a></li>
      </ul>
    </div>
    <div>
      <h4>Contact Us</h4>
      <p>+1 (855) ONE-ZURN<br>+1 (855) 663-9876</p>
      <p style="margin-top: 8px;">
        <a href="https://www.zurn.com/" target="_blank">zurn.com</a><br>
        <a href="https://www.elkay.com/" target="_blank">elkay.com</a><br>
        <a href="https://zurnelkay.com/" target="_blank">zurnelkay.com</a>
      </p>
    </div>
  </div>
  <div class="ze-footer-bottom">
    &copy; {{ 'now' | date: '%Y' }} Zurn Elkay Water Solutions. All rights reserved.
  </div>
</footer>
'@

  Write-Host "  Updating Footer template..." -ForegroundColor Cyan
  $result = Invoke-DataversePatch `
    -EntitySet "adx_webtemplates" `
    -RecordId ([guid]$footerTemplate.adx_webtemplateid) `
    -Body @{ adx_source = $footerSource }
  if ($result) {
    Write-Host "  Footer template updated successfully." -ForegroundColor Green
  } else {
    Write-Warning "  Failed to update Footer template."
  }
}

# ============================================================
# Step 4: Update Home Page Content
# ============================================================
Write-StepHeader "4" "Updating Home Page Content"

# Find the Home page - look for root page first, then content page
$homeRoot = $null
$homeContent = $null

if ($pages -and $pages.Count -gt 0) {
  # Find root Home page (isroot=true, name='Home' or partialurl='/')
  foreach ($p in $pages) {
    if ($p.adx_name -eq "Home" -and $p.adx_isroot -eq $true) {
      $homeRoot = $p
      break
    }
  }
  # Fallback: look for root page by partial URL
  if (-not $homeRoot) {
    foreach ($p in $pages) {
      if ($p.adx_partialurl -eq "/" -and $p.adx_isroot -eq $true) {
        $homeRoot = $p
        break
      }
    }
  }

  if ($homeRoot) {
    Write-Host "  Found Home root page: $($homeRoot.adx_name) [$($homeRoot.adx_webpageid)]" -ForegroundColor Green

    # Find the content page (child of root with same name or matching parent)
    foreach ($p in $pages) {
      if ($p._adx_parentpageid_value -eq $homeRoot.adx_webpageid) {
        if ($p.adx_name -eq "Home" -or $p.adx_partialurl -eq "/") {
          $homeContent = $p
          break
        }
      }
    }
    # If no content page found, the root page IS the content page
    if (-not $homeContent) {
      $homeContent = $homeRoot
      Write-Host "  Using root page as content page (no child found)." -ForegroundColor DarkGray
    } else {
      Write-Host "  Found Home content page: $($homeContent.adx_webpageid)" -ForegroundColor Green
    }
  } else {
    Write-Warning "Could not find Home page. Listing available pages:"
    foreach ($p in $pages) {
      Write-Host "    $($p.adx_name) | /$($p.adx_partialurl) | root=$($p.adx_isroot)" -ForegroundColor DarkGray
    }
  }
}

if ($homeContent) {
  $homeHtml = @'
<!-- Zurn Elkay Support Center Home Page -->

<div class="ze-hero">
  <h1>What can we help you with?</h1>
  <p>Search our knowledge base, browse by product, or submit a service request</p>
</div>

<h2 class="ze-section-title">Browse by Product Category</h2>
<div class="ze-grid">

  <a href="/knowledgebase/" class="ze-tile ze-tile-hydration">
    <div class="ze-tile-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>
      </svg>
    </div>
    <h3>Hydration</h3>
    <p>Bottle Filling Stations, Water Coolers &amp; Drinking Fountains</p>
  </a>

  <a href="/knowledgebase/" class="ze-tile ze-tile-sinks">
    <div class="ze-tile-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="10" width="18" height="4" rx="1"/>
        <path d="M12 4v6M8 14v4a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-4"/>
      </svg>
    </div>
    <h3>Sinks &amp; Faucets</h3>
    <p>Stainless Steel Sinks, Undermount Sinks &amp; Sensor Faucets</p>
  </a>

  <a href="/knowledgebase/" class="ze-tile ze-tile-flush">
    <div class="ze-tile-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 6v6l4 2"/>
      </svg>
    </div>
    <h3>Flush Valves</h3>
    <p>Sensor Flush Valves, Retrofit Kits &amp; Urinal Valves</p>
  </a>

  <a href="/knowledgebase/" class="ze-tile ze-tile-drainage">
    <div class="ze-tile-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2"/>
        <circle cx="8.5" cy="8.5" r="1.5"/>
        <circle cx="15.5" cy="8.5" r="1.5"/>
        <circle cx="8.5" cy="15.5" r="1.5"/>
        <circle cx="15.5" cy="15.5" r="1.5"/>
        <circle cx="12" cy="12" r="1.5"/>
      </svg>
    </div>
    <h3>Drainage</h3>
    <p>Floor Drains, Trench Drains &amp; Roof Drains</p>
  </a>

  <a href="/knowledgebase/" class="ze-tile ze-tile-backflow">
    <div class="ze-tile-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
    </div>
    <h3>Backflow Prevention</h3>
    <p>RPZ Assemblies &amp; Double Check Valves by Wilkins</p>
  </a>

  <a href="/knowledgebase/" class="ze-tile ze-tile-filtration">
    <div class="ze-tile-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
      </svg>
    </div>
    <h3>Filtration</h3>
    <p>Water Sentry Filters &amp; Replacement Cartridges</p>
  </a>

</div>

<h2 class="ze-section-title">How Can We Help?</h2>
<div class="ze-action-grid">

  <a href="/support/create-case/" class="ze-action-card">
    <div class="ze-action-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="12" y1="18" x2="12" y2="12"/>
        <line x1="9" y1="15" x2="15" y2="15"/>
      </svg>
    </div>
    <h3>Submit a Request</h3>
    <p>Open a new support case and our team will respond promptly</p>
  </a>

  <a href="/support/" class="ze-action-card">
    <div class="ze-action-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10 9 9 9 8 9"/>
      </svg>
    </div>
    <h3>Track My Cases</h3>
    <p>View status and updates on your open support requests</p>
  </a>

  <a href="/knowledgebase/" class="ze-action-card">
    <div class="ze-action-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
        <circle cx="12" cy="10" r="3"/>
        <line x1="12" y1="13" x2="12" y2="15"/>
      </svg>
    </div>
    <h3>Knowledge Base</h3>
    <p>Browse articles, troubleshooting guides &amp; product documentation</p>
  </a>

</div>
'@

  Write-Host "  Updating Home page content..." -ForegroundColor Cyan
  $result = Invoke-DataversePatch `
    -EntitySet "adx_webpages" `
    -RecordId ([guid]$homeContent.adx_webpageid) `
    -Body @{ adx_copy = $homeHtml }
  if ($result) {
    Write-Host "  Home page updated successfully." -ForegroundColor Green
  } else {
    Write-Warning "  Failed to update Home page content."
  }
} else {
  Write-Warning "Could not find Home page to update."
}

# ============================================================
# Step 5: Omnichannel Chat Widget (Discovery)
# ============================================================
Write-StepHeader "5" "Omnichannel Chat Widget"

Write-Host "  Checking for Live Chat configuration..." -ForegroundColor Cyan
$chatConfigs = $null
try {
  $chatConfigs = Invoke-DataverseGet -EntitySet "msdyn_livechatconfigs" `
    -Select "msdyn_livechatconfigid,msdyn_widgetappid,msdyn_orgurl,msdyn_orgid" `
    -Top 5
} catch {
  Write-Host "  Could not query msdyn_livechatconfigs (entity may not be accessible via Web API)." -ForegroundColor Yellow
  Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor DarkGray
  Write-Host "  Chat widget can be embedded manually via Admin Center." -ForegroundColor Yellow
}

if ($chatConfigs -and $chatConfigs.Count -gt 0) {
  Write-Host "  Found $($chatConfigs.Count) chat config(s):" -ForegroundColor Green
  foreach ($cc in $chatConfigs) {
    Write-Host "    Widget App ID: $($cc.msdyn_widgetappid)"
    Write-Host "    Org URL:       $($cc.msdyn_orgurl)"
    Write-Host "    Org ID:        $($cc.msdyn_orgid)"
    Write-Host ""
  }

  # Use the first config to generate the widget script
  $widgetAppId = $chatConfigs[0].msdyn_widgetappid
  $orgUrl = $chatConfigs[0].msdyn_orgurl
  $orgId = $chatConfigs[0].msdyn_orgid

  if ($widgetAppId -and $orgUrl -and $orgId) {
    Write-Host "  To add the chat widget, add this script to your portal footer or via" -ForegroundColor Yellow
    Write-Host "  Admin Center > Customer Support > Chat Widgets > Install:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  <script" -ForegroundColor DarkGray
    Write-Host "    id=`"Microsoft_Omnichannel_LCWidget`"" -ForegroundColor DarkGray
    Write-Host "    src=`"https://oc-cdn-public.azureedge.net/livechatwidget/scripts/LiveChatBootstrapper.js`"" -ForegroundColor DarkGray
    Write-Host "    data-app-id=`"$widgetAppId`"" -ForegroundColor DarkGray
    Write-Host "    data-org-id=`"$orgId`"" -ForegroundColor DarkGray
    Write-Host "    data-org-url=`"$orgUrl`"" -ForegroundColor DarkGray
    Write-Host "  ></script>" -ForegroundColor DarkGray
    Write-Host ""

    # Optionally inject into Footer template
    if ($footerTemplate) {
      Write-Host "  Injecting chat widget script into Footer template..." -ForegroundColor Cyan

      $chatScript = @"
<script
  id="Microsoft_Omnichannel_LCWidget"
  src="https://oc-cdn-public.azureedge.net/livechatwidget/scripts/LiveChatBootstrapper.js"
  data-app-id="$widgetAppId"
  data-org-id="$orgId"
  data-org-url="$orgUrl"
></script>
"@
      # Append chat script to the footer source
      $fullFooter = $footerSource + "`n`n" + $chatScript

      $result = Invoke-DataversePatch `
        -EntitySet "adx_webtemplates" `
        -RecordId ([guid]$footerTemplate.adx_webtemplateid) `
        -Body @{ adx_source = $fullFooter }
      if ($result) {
        Write-Host "  Chat widget injected into Footer." -ForegroundColor Green
      } else {
        Write-Warning "  Failed to inject chat widget."
      }
    }
  } else {
    Write-Host "  Chat config found but missing widget parameters." -ForegroundColor Yellow
    Write-Host "  Configure the chat widget in D365 Admin Center first." -ForegroundColor Yellow
  }
} else {
  Write-Host "  No Live Chat configuration found." -ForegroundColor DarkGray
  Write-Host "  The Omnichannel chat widget will be configured after portal setup." -ForegroundColor DarkGray
  Write-Host "  Go to D365 Admin Center > Customer Support > Chat > configure the widget," -ForegroundColor DarkGray
  Write-Host "  then re-run this script to inject it." -ForegroundColor DarkGray
}

# ============================================================
# Step 6: Verify & Clear Cache Reminder
# ============================================================
Write-StepHeader "6" "Summary & Next Steps"

Write-Host "  Portal branding applied:" -ForegroundColor Green
Write-Host "    [x] Header - Zurn Elkay navy bar with logo, nav, and auth" -ForegroundColor White
Write-Host "    [x] Footer - Company info, quick links, contact details" -ForegroundColor White
Write-Host "    [x] Home   - Hero banner, 6 product category tiles, 3 quick actions" -ForegroundColor White
Write-Host "    [x] CSS    - Brand colors, responsive grid, hover effects" -ForegroundColor White
if ($chatConfigs -and $chatConfigs.Count -gt 0 -and $chatConfigs[0].msdyn_widgetappid) {
  Write-Host "    [x] Chat   - Omnichannel widget script injected in footer" -ForegroundColor White
} else {
  Write-Host "    [ ] Chat   - Configure in Admin Center, then re-run" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  IMPORTANT: Clear the portal cache to see changes:" -ForegroundColor Yellow
Write-Host "    1. Go to your portal URL" -ForegroundColor White
Write-Host "    2. Append /_services/about to the URL" -ForegroundColor White
Write-Host "    3. Click 'Clear Cache'" -ForegroundColor White
Write-Host "    OR wait ~15 minutes for automatic cache refresh" -ForegroundColor White
Write-Host ""
Write-Host "  Portal URL: https://zurnelkaycustomercare.powerappsportals.com/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Done!" -ForegroundColor Green
