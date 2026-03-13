<#
.SYNOPSIS
    Redesigns the Knowledge Base Home page to match Elkay's Salesforce portal style.
.DESCRIPTION
    Updates the "Knowledge Base - Home" web template for the Zurn Elkay Customer Care
    portal with:
      - Hero banner with search (navy/blue gradient)
      - 8 product category tiles with Font Awesome icons
      - Top Articles section (dynamic via FetchXML)
      - Contact Support call-to-action
.NOTES
    Run with: .\16-KBPage.ps1
    Requires: DataverseHelper.psm1, az login
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Import-Module "$scriptDir\DataverseHelper.psm1" -Force

Connect-Dataverse

$siteId = "2dd891fe-1418-f111-8342-7c1e52143136"

# ============================================================
# Step 1: Find the KB Home web template for our site
# ============================================================
Write-StepHeader "1" "Finding KB Home Web Template"

$kbTemplates = Invoke-DataverseGet -EntitySet "adx_webtemplates" `
    -Filter "_adx_websiteid_value eq $siteId and adx_name eq 'Knowledge Base - Home'" `
    -Select "adx_webtemplateid,adx_name,adx_source"

if (-not $kbTemplates -or $kbTemplates.Count -eq 0) {
    Write-Error "Could not find 'Knowledge Base - Home' template for site $siteId"
    return
}

$kbTemplate = $kbTemplates[0]
$kbTemplateId = $kbTemplate.adx_webtemplateid
Write-Host "  Found template: $($kbTemplate.adx_name) ($kbTemplateId)" -ForegroundColor Green
Write-Host "  Current source length: $($kbTemplate.adx_source.Length) chars" -ForegroundColor DarkGray

# ============================================================
# Step 2: Build the new KB Home template
# ============================================================
Write-StepHeader "2" "Building Elkay-Inspired KB Home Template"

$kbSource = @'
{% extends 'Layout 1 Column' %}

{% block main %}
<style>
  /* ===== KB Hero ===== */
  .ze-kb-hero {
    background: linear-gradient(135deg, #002855 0%, #004080 50%, #0072CE 100%);
    padding: 65px 20px;
    text-align: center;
    border-radius: 0;
    margin: -20px -15px 40px -15px;
    position: relative;
    overflow: hidden;
  }
  .ze-kb-hero::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(ellipse at 30% 50%, rgba(0,181,173,0.15) 0%, transparent 60%),
                radial-gradient(ellipse at 70% 30%, rgba(0,114,206,0.2) 0%, transparent 50%);
    pointer-events: none;
  }
  .ze-kb-hero h1 {
    color: #fff;
    font-size: 2.4rem;
    font-weight: 700;
    margin-bottom: 8px;
    position: relative;
    z-index: 1;
  }
  .ze-kb-hero .subtitle {
    color: rgba(255,255,255,0.85);
    font-size: 1.1rem;
    margin-bottom: 28px;
    position: relative;
    z-index: 1;
  }
  .ze-kb-search-wrap {
    max-width: 620px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
  }
  .ze-kb-search-wrap form {
    display: flex;
    background: #fff;
    border-radius: 30px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
  }
  .ze-kb-search-wrap input[type="text"] {
    flex: 1;
    border: none;
    padding: 16px 25px;
    font-size: 1rem;
    outline: none;
    background: transparent;
    color: #333;
  }
  .ze-kb-search-wrap input[type="text"]::placeholder {
    color: #999;
  }
  .ze-kb-search-wrap button {
    background: #00B5AD;
    color: #fff;
    border: none;
    padding: 16px 32px;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 600;
    transition: background 0.2s;
    white-space: nowrap;
  }
  .ze-kb-search-wrap button:hover {
    background: #009990;
  }

  /* ===== Section Headings ===== */
  .ze-kb-section-title {
    text-align: center;
    color: #002855;
    font-size: 1.6rem;
    font-weight: 700;
    margin-bottom: 35px;
    position: relative;
  }
  .ze-kb-section-title::after {
    content: '';
    display: block;
    width: 60px;
    height: 3px;
    background: #00B5AD;
    margin: 12px auto 0;
    border-radius: 2px;
  }

  /* ===== Category Tiles ===== */
  .ze-kb-categories {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 22px;
    margin-bottom: 55px;
    padding: 0;
  }
  @media (max-width: 992px) {
    .ze-kb-categories { grid-template-columns: repeat(2, 1fr); gap: 16px; }
  }
  @media (max-width: 480px) {
    .ze-kb-categories { grid-template-columns: 1fr; }
  }
  .ze-kb-tile {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 32px 18px 28px;
    background: #fff;
    border: 1px solid #e8ecf0;
    border-radius: 12px;
    text-decoration: none !important;
    color: #002855;
    transition: all 0.3s ease;
    text-align: center;
    min-height: 155px;
    position: relative;
    overflow: hidden;
  }
  .ze-kb-tile::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #0072CE, #00B5AD);
    transform: scaleX(0);
    transition: transform 0.3s ease;
  }
  .ze-kb-tile:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 30px rgba(0,40,85,0.12);
    border-color: #0072CE;
    text-decoration: none !important;
    color: #0072CE;
  }
  .ze-kb-tile:hover::before {
    transform: scaleX(1);
  }
  .ze-kb-tile .tile-icon {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: linear-gradient(135deg, #e8f4fd 0%, #d0ecf9 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 14px;
    transition: all 0.3s ease;
  }
  .ze-kb-tile .tile-icon i {
    font-size: 1.5rem;
    color: #0072CE;
    transition: color 0.3s ease;
  }
  .ze-kb-tile:hover .tile-icon {
    background: linear-gradient(135deg, #002855, #0072CE);
  }
  .ze-kb-tile:hover .tile-icon i {
    color: #fff;
  }
  .ze-kb-tile .tile-label {
    font-size: 0.95rem;
    font-weight: 600;
    line-height: 1.3;
  }

  /* ===== Top Articles ===== */
  .ze-kb-articles-section {
    margin-bottom: 45px;
  }
  .ze-kb-articles-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0 40px;
  }
  @media (max-width: 768px) {
    .ze-kb-articles-grid { grid-template-columns: 1fr; }
  }
  .ze-kb-article-item {
    padding: 14px 0;
    border-bottom: 1px solid #eef0f2;
    display: flex;
    align-items: flex-start;
    gap: 12px;
  }
  .ze-kb-article-item .art-icon {
    color: #00B5AD;
    margin-top: 2px;
    flex-shrink: 0;
  }
  .ze-kb-article-item a {
    color: #0072CE;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.95rem;
    line-height: 1.4;
    transition: color 0.2s;
  }
  .ze-kb-article-item a:hover {
    color: #002855;
    text-decoration: underline;
  }

  /* ===== Contact Support CTA ===== */
  .ze-kb-contact {
    text-align: center;
    padding: 45px 30px;
    background: linear-gradient(135deg, #f5f8fb 0%, #eef2f7 100%);
    border-radius: 12px;
    margin-bottom: 30px;
  }
  .ze-kb-contact h3 {
    color: #002855;
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 8px;
  }
  .ze-kb-contact p {
    color: #5a6a7a;
    font-size: 1rem;
    margin-bottom: 22px;
  }
  .ze-kb-contact .btn-contact {
    background: #002855;
    color: #fff !important;
    padding: 13px 38px;
    border-radius: 25px;
    text-decoration: none !important;
    font-weight: 600;
    font-size: 1rem;
    display: inline-block;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(0,40,85,0.2);
  }
  .ze-kb-contact .btn-contact:hover {
    background: #0072CE;
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(0,40,85,0.3);
  }
  .ze-kb-contact .btn-chat {
    background: transparent;
    color: #0072CE !important;
    padding: 13px 38px;
    border-radius: 25px;
    border: 2px solid #0072CE;
    text-decoration: none !important;
    font-weight: 600;
    font-size: 1rem;
    display: inline-block;
    transition: all 0.3s ease;
    margin-left: 12px;
  }
  .ze-kb-contact .btn-chat:hover {
    background: #0072CE;
    color: #fff !important;
  }
</style>

<!-- ===== Hero Section ===== -->
<div class="ze-kb-hero">
  <h1>What can we help you with?</h1>
  <p class="subtitle">Search our knowledge base for product guides, troubleshooting, and support articles</p>
  <div class="ze-kb-search-wrap">
    <form action="/search" method="GET">
      <input type="text" name="q" placeholder="Search for articles, products, or topics..." aria-label="Search knowledge base" />
      <button type="submit"><i class="fa fa-search"></i>&nbsp; Search</button>
    </form>
  </div>
</div>

<!-- ===== Browse by Category ===== -->
<h2 class="ze-kb-section-title">Browse by Category</h2>
<div class="ze-kb-categories">
  <a href="/search?q=bottle+filling+station" class="ze-kb-tile">
    <div class="tile-icon"><i class="fa fa-tint"></i></div>
    <div class="tile-label">Bottle Filling<br/>Stations</div>
  </a>
  <a href="/search?q=cooler+fountain+drinking" class="ze-kb-tile">
    <div class="tile-icon"><i class="fa fa-snowflake-o"></i></div>
    <div class="tile-label">Coolers &amp;<br/>Fountains</div>
  </a>
  <a href="/search?q=water+dispenser" class="ze-kb-tile">
    <div class="tile-icon"><i class="fa fa-glass"></i></div>
    <div class="tile-label">Water<br/>Dispensers</div>
  </a>
  <a href="/search?q=sink+faucet" class="ze-kb-tile">
    <div class="tile-icon"><i class="fa fa-shower"></i></div>
    <div class="tile-label">Sinks &amp;<br/>Faucets</div>
  </a>
  <a href="/search?q=outdoor+installation" class="ze-kb-tile">
    <div class="tile-icon"><i class="fa fa-sun-o"></i></div>
    <div class="tile-label">Outdoor</div>
  </a>
  <a href="/search?q=accessories+parts+replacement" class="ze-kb-tile">
    <div class="tile-icon"><i class="fa fa-cogs"></i></div>
    <div class="tile-label">Accessories</div>
  </a>
  <a href="/search?q=filter+filtration+cartridge" class="ze-kb-tile">
    <div class="tile-icon"><i class="fa fa-filter"></i></div>
    <div class="tile-label">Filtration</div>
  </a>
  <a href="/search?q=installation+guide+manual+specification" class="ze-kb-tile">
    <div class="tile-icon"><i class="fa fa-book"></i></div>
    <div class="tile-label">Resources</div>
  </a>
</div>

<!-- ===== Top Articles ===== -->
<div class="ze-kb-articles-section">
  <h2 class="ze-kb-section-title">Top Articles</h2>
  <div class="ze-kb-articles-grid">
    {% fetchxml articles_query %}
    <fetch top="8">
      <entity name="knowledgearticle">
        <attribute name="title" />
        <attribute name="knowledgearticleid" />
        <attribute name="articlepublicnumber" />
        <filter>
          <condition attribute="isrootarticle" operator="eq" value="0" />
          <condition attribute="statecode" operator="eq" value="3" />
        </filter>
        <order attribute="createdon" descending="true" />
      </entity>
    </fetch>
    {% endfetchxml %}
    {% for article in articles_query.results.entities %}
      <div class="ze-kb-article-item">
        <span class="art-icon"><i class="fa fa-file-text-o"></i></span>
        <a href="/knowledgebase/article/{{ article.articlepublicnumber }}">{{ article.title }}</a>
      </div>
    {% endfor %}
    {% if articles_query.results.entities.size == 0 %}
      <div class="ze-kb-article-item">
        <span class="art-icon"><i class="fa fa-info-circle"></i></span>
        <span style="color: #5a6a7a;">Knowledge base articles are being prepared. Check back soon.</span>
      </div>
    {% endif %}
  </div>
</div>

<!-- ===== Contact Support CTA ===== -->
<div class="ze-kb-contact">
  <h3>Can't find what you're looking for?</h3>
  <p>Our technical support team is ready to help with any questions about Zurn Elkay products.</p>
  <a href="/support/create-case/" class="btn-contact"><i class="fa fa-envelope"></i>&nbsp; Submit a Request</a>
  <a href="javascript:void(0);" onclick="Microsoft.Omnichannel.LiveChatWidget.SDK.startChat();" class="btn-chat"><i class="fa fa-comments"></i>&nbsp; Live Chat</a>
</div>

{% endblock %}
'@

Write-Host "  New template source: $($kbSource.Length) chars" -ForegroundColor Green

# ============================================================
# Step 3: Update the KB Home web template
# ============================================================
Write-StepHeader "3" "Updating KB Home Web Template"

$patchBody = @{
    adx_source = $kbSource
}

$apiUrl = Get-DataverseApiUrl
$headers = Get-DataverseHeaders
$patchUrl = "$apiUrl/adx_webtemplates($kbTemplateId)"
$jsonBody = $patchBody | ConvertTo-Json -Depth 5

try {
    Invoke-RestMethod -Uri $patchUrl -Method Patch -Headers $headers -Body $jsonBody -ContentType "application/json; charset=utf-8" -ErrorAction Stop
    Write-Host "  KB Home template updated successfully!" -ForegroundColor Green
} catch {
    Write-Error "Failed to update KB Home template: $($_.Exception.Message)"
    if ($_.ErrorDetails.Message) {
        Write-Error $_.ErrorDetails.Message
    }
    return
}

# ============================================================
# Step 4: Verify the update
# ============================================================
Write-StepHeader "4" "Verifying Update"

$verify = Invoke-DataverseGet -EntitySet "adx_webtemplates" `
    -Filter "adx_webtemplateid eq $kbTemplateId" `
    -Select "adx_name,adx_source"

if ($verify -and $verify.Count -gt 0) {
    $newLen = 0
    if ($verify[0].adx_source) { $newLen = $verify[0].adx_source.Length }
    Write-Host "  Template: $($verify[0].adx_name)" -ForegroundColor Green
    Write-Host "  New source length: $newLen chars" -ForegroundColor Green
    
    if ($newLen -gt 1000) {
        Write-Host "  Template updated successfully with Elkay-inspired design!" -ForegroundColor Green
    } else {
        Write-Warning "Template source seems too short. Something may have gone wrong."
    }
} else {
    Write-Warning "Could not verify template update."
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " KB Page Redesign Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Features applied:" -ForegroundColor White
Write-Host "  - Hero banner with search (navy/blue gradient)" -ForegroundColor White
Write-Host "  - 8 product category tiles matching Elkay Salesforce layout" -ForegroundColor White
Write-Host "  - Top Articles section (dynamic from published KB articles)" -ForegroundColor White
Write-Host "  - Contact Support CTA with Submit Request + Live Chat" -ForegroundColor White
Write-Host ""
Write-Host "Clear portal cache to see changes:" -ForegroundColor Yellow
Write-Host "  https://zurnelkaycustomercare.powerappsportals.com/_services/about" -ForegroundColor Yellow
Write-Host ""
