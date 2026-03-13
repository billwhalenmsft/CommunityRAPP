$ErrorActionPreference = "Stop"
$root = "C:\Users\billwhalen\OneDrive - Microsoft\Documents\GitHub\Demo Setups\Zurn Elkay Demo"
$d = Get-Content "$root\data\report-data.json" -Raw | ConvertFrom-Json

# Build account lookup by ID
$acctLookup = @{}
foreach ($a in $d.accounts) { $acctLookup[$a.accountid] = $a.name }

# Classify accounts
$mfgAccounts = @($d.accounts | Where-Object { $_.name -match 'Zurn|Elkay' })
$distAccounts = @($d.accounts | Where-Object { $_.name -match 'Ferguson|Hajoca|Winsupply|HD Supply|Wolseley|Consolidated|Pacific|Midwest|Southern|Gateway|ABC|Metro|Lakeside' })
$euAccounts = @($d.accounts | Where-Object { $_.name -match 'Greenfield|Mesa|Marriott|Johnson' })

# Classify contacts
$stakeContacts = @($d.contacts | Where-Object { $_.emailaddress1 -match '@zurn\.com' })
$distContacts = @($d.contacts | Where-Object { $_.emailaddress1 -notmatch '@zurn\.com' -and $_.emailaddress1 -notmatch '@greenfieldsd|@mesaaz|@marriott|@gmail' })
$euContacts = @($d.contacts | Where-Object { $_.emailaddress1 -match '@greenfieldsd|@mesaaz|@marriott|@gmail' })

# Classify products
$zurnProducts = @($d.products | Where-Object { $_.productnumber -match '^ZN-|^WK-' })
$elkayProducts = @($d.products | Where-Object { $_.productnumber -match '^EK-' })

# Classify queues
$zurnQueues = @($d.queues | Where-Object { $_.name -match 'Zurn' })
$elkayQueues = @($d.queues | Where-Object { $_.name -match 'Elkay' })

# Subject parents
$parentSubjects = @($d.subjects | Where-Object { $null -eq $_._parentsubject_value -or $_._parentsubject_value -eq '' })
$childSubjects = @($d.subjects | Where-Object { $null -ne $_._parentsubject_value -and $_._parentsubject_value -ne '' })

# Case stats
$activeCases = @($d.cases | Where-Object { $_.statecode -eq 0 })
$resolvedCases = @($d.cases | Where-Object { $_.statecode -eq 1 })
$otherCases = @($d.cases | Where-Object { $_.statecode -ne 0 -and $_.statecode -ne 1 })

# Priority/Origin maps
function Get-PriorityLabel($code) { switch ($code) { 1 { "High" } 2 { "Normal" } 3 { "Low" } default { "Unknown" } } }
function Get-OriginLabel($code)   { switch ($code) { 1 { "Phone" } 2 { "Email" } 3 { "Web" } default { "Other" } } }
function Get-StateLabel($code)    { switch ($code) { 0 { "Active" } 1 { "Resolved" } 2 { "Cancelled" } default { "Other" } } }

$p1 = @($d.cases | Where-Object { $_.prioritycode -eq 1 }).Count
$p2 = @($d.cases | Where-Object { $_.prioritycode -eq 2 }).Count
$p3 = @($d.cases | Where-Object { $_.prioritycode -eq 3 }).Count
$oEmail = @($d.cases | Where-Object { $_.caseorigincode -eq 2 }).Count
$oPhone = @($d.cases | Where-Object { $_.caseorigincode -eq 1 }).Count
$oWeb = @($d.cases | Where-Object { $_.caseorigincode -eq 3 }).Count

$timestamp = Get-Date -Format "MMMM d, yyyy 'at' h:mm tt"

# --- Build account rows ---
function Build-AccountRow($a, $type, $tier) {
    $city = if ($a.address1_city) { "$($a.address1_city), $($a.address1_stateorprovince)" } else { "-" }
    $tierBadge = if ($tier) { "<span class='badge tier-$tier'>Tier $tier</span>" } else { "" }
    return "<tr><td>$($a.name)</td><td>$type $tierBadge</td><td>$city</td><td>$($a.telephone1)</td></tr>"
}

$acctRows = ""
foreach ($a in $mfgAccounts) { $acctRows += Build-AccountRow $a "Manufacturer" "" }
foreach ($a in $distAccounts) {
    $tier = if ($a.accountnumber -match 'TIER-(\d)') { $Matches[1] } else { "" }
    $acctRows += Build-AccountRow $a "Distributor" $tier
}
foreach ($a in $euAccounts) { $acctRows += Build-AccountRow $a "End User" "" }

# --- Build contact rows ---
$contactRows = ""
foreach ($c in $d.contacts) {
    $acctName = if ($c.accountName) { $c.accountName } elseif ($c._parentcustomerid_value -and $acctLookup.ContainsKey($c._parentcustomerid_value)) { $acctLookup[$c._parentcustomerid_value] } else { "-" }
    $cat = if ($c.emailaddress1 -match '@zurn\.com') { "Stakeholder" } elseif ($c.emailaddress1 -match '@greenfieldsd|@mesaaz|@marriott|@gmail') { "End User" } else { "Distributor" }
    $contactRows += "<tr><td>$($c.fullname)</td><td>$($c.jobtitle)</td><td>$acctName</td><td>$cat</td><td>$($c.emailaddress1)</td></tr>"
}

# --- Build product rows ---
$productRows = ""
foreach ($p in $d.products) {
    $brand = if ($p.productnumber -match '^ZN-') { "Zurn" } elseif ($p.productnumber -match '^EK-') { "Elkay" } else { "Wilkins" }
    $state = if ($p.statecode -eq 0) { "<span class='badge active'>Active</span>" } else { "<span class='badge draft'>Draft</span>" }
    $priceStr = if ($p.price) { "`${0:N2}" -f $p.price } else { "-" }
    $productRows += "<tr><td>$($p.productnumber)</td><td>$($p.name)</td><td>$brand</td><td>$state</td></tr>"
}

# --- Build queue rows ---
$queueRows = ""
foreach ($q in ($d.queues | Sort-Object name)) {
    $brand = if ($q.name -match 'Zurn') { "Zurn" } else { "Elkay" }
    $channel = if ($q.name -match 'Phone') { "Phone" } else { "Email" }
    $queueRows += "<tr><td>$($q.name)</td><td>$brand</td><td>$channel</td><td>$($q.emailaddress)</td></tr>"
}

# --- Build subject rows ---
$subjectRows = ""
foreach ($s in ($d.subjects | Sort-Object title)) {
    $isParent = ($null -eq $s._parentsubject_value -or $s._parentsubject_value -eq '')
    $indent = if ($isParent) { "<strong>$($s.title)</strong>" } else { "&nbsp;&nbsp;&nbsp;&nbsp;$($s.title)" }
    $desc = if ($s.description) { $s.description } else { "-" }
    $subjectRows += "<tr><td>$indent</td><td>$desc</td></tr>"
}

# --- Build case rows (sorted by priority then title) ---
$caseRows = ""
foreach ($c in ($d.cases | Sort-Object @{E={$_.statecode}}, @{E={$_.prioritycode}}, @{E={$_.title}})) {
    $pri = Get-PriorityLabel $c.prioritycode
    $priClass = switch ($c.prioritycode) { 1 { "high" } 2 { "normal" } 3 { "low" } default { "" } }
    $origin = Get-OriginLabel $c.caseorigincode
    $state = Get-StateLabel $c.statecode
    $stateClass = if ($c.statecode -eq 0) { "active" } elseif ($c.statecode -eq 1) { "resolved" } else { "other" }
    $caseRows += "<tr><td>$($c.ticketnumber)</td><td>$($c.title)</td><td><span class='badge priority-$priClass'>$pri</span></td><td>$origin</td><td><span class='badge state-$stateClass'>$state</span></td></tr>"
}

# --- SLA info ---
$slaName = if ($d.slas.Count -gt 0) { $d.slas[0].name } else { "N/A" }
$slaState = if ($d.slas.Count -gt 0) { if ($d.slas[0].statecode -eq 0) { "Draft" } else { "Active" } } else { "N/A" }
$slaItemsHtml = ""
foreach ($si in $d.slaItems) {
    $failHrs = [math]::Round($si.failureafter / 60, 1)
    $warnHrs = [math]::Round($si.warnafter / 60, 1)
    $slaItemsHtml += "<tr><td>$($si.name)</td><td>${failHrs}h</td><td>${warnHrs}h</td></tr>"
}

# --- Generate HTML ---
$html = @"
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Zurn Elkay Demo - Data Overview</title>
<style>
  :root {
    --zurn-blue: #003B71;
    --elkay-teal: #00838F;
    --bg: #f5f7fa;
    --card-bg: #ffffff;
    --border: #e2e8f0;
    --text: #1a202c;
    --text-muted: #718096;
    --success: #38a169;
    --warning: #d69e2e;
    --danger: #e53e3e;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
  
  .header {
    background: linear-gradient(135deg, var(--zurn-blue) 0%, var(--elkay-teal) 100%);
    color: white; padding: 2rem 2rem 1.5rem; margin-bottom: 2rem;
  }
  .header h1 { font-size: 2rem; font-weight: 700; margin-bottom: 0.25rem; }
  .header p { opacity: 0.85; font-size: 0.95rem; }
  .header .env-info { margin-top: 1rem; font-size: 0.85rem; opacity: 0.7; font-family: 'Cascadia Code', 'Consolas', monospace; }
  
  .container { max-width: 1200px; margin: 0 auto; padding: 0 1.5rem 3rem; }
  
  .stats-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin-bottom: 2rem;
  }
  .stat-card {
    background: var(--card-bg); border-radius: 12px; padding: 1.25rem; text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08); border: 1px solid var(--border);
  }
  .stat-card .number { font-size: 2rem; font-weight: 700; color: var(--zurn-blue); }
  .stat-card .label { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.25rem; }
  
  .section { margin-bottom: 2rem; }
  .section-header {
    display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; cursor: pointer;
  }
  .section-header h2 { font-size: 1.25rem; color: var(--zurn-blue); }
  .section-header .count { background: var(--zurn-blue); color: white; font-size: 0.75rem; padding: 0.15rem 0.6rem; border-radius: 12px; font-weight: 600; }
  .section-header .toggle { color: var(--text-muted); transition: transform 0.2s; font-size: 0.8rem; }
  .section-header .toggle.collapsed { transform: rotate(-90deg); }
  
  .card {
    background: var(--card-bg); border-radius: 12px; overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08); border: 1px solid var(--border);
  }
  
  table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
  thead { background: #f8fafc; }
  th { text-align: left; padding: 0.75rem 1rem; font-weight: 600; color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid var(--border); }
  td { padding: 0.625rem 1rem; border-bottom: 1px solid #f1f5f9; }
  tr:last-child td { border-bottom: none; }
  tr:hover { background: #f8fafc; }
  
  .badge {
    display: inline-block; padding: 0.15rem 0.5rem; border-radius: 6px; font-size: 0.75rem; font-weight: 600;
  }
  .badge.active { background: #c6f6d5; color: #22543d; }
  .badge.draft { background: #fefcbf; color: #744210; }
  .badge.resolved, .badge.state-resolved { background: #bee3f8; color: #2a4365; }
  .badge.state-active { background: #c6f6d5; color: #22543d; }
  .badge.state-other { background: #e2e8f0; color: #4a5568; }
  .badge.priority-high { background: #fed7d7; color: #9b2c2c; }
  .badge.priority-normal { background: #fefcbf; color: #744210; }
  .badge.priority-low { background: #e2e8f0; color: #4a5568; }
  .badge.tier-1 { background: #fed7d7; color: #9b2c2c; }
  .badge.tier-2 { background: #fefcbf; color: #744210; }
  .badge.tier-3 { background: #bee3f8; color: #2a4365; }
  .badge.tier-4 { background: #e2e8f0; color: #4a5568; }
  
  .sla-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; padding: 1.25rem; }
  .sla-detail { }
  .sla-detail .label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
  .sla-detail .value { font-size: 1.1rem; font-weight: 600; margin-top: 0.25rem; }
  
  .mini-stats { display: flex; gap: 1.5rem; padding: 1rem 1.25rem; background: #f8fafc; border-bottom: 1px solid var(--border); flex-wrap: wrap; }
  .mini-stat .num { font-weight: 700; color: var(--zurn-blue); }
  .mini-stat .lbl { font-size: 0.8rem; color: var(--text-muted); margin-left: 0.25rem; }
  
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
  @media (max-width: 768px) { .two-col { grid-template-columns: 1fr; } }
  
  .footer { text-align: center; color: var(--text-muted); font-size: 0.8rem; margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid var(--border); }

  .collapsible-content { max-height: 2000px; overflow: hidden; transition: max-height 0.3s ease; }
  .collapsible-content.collapsed { max-height: 0; }
</style>
</head>
<body>

<div class="header">
  <h1>Zurn Elkay Demo Environment</h1>
  <p>D365 Customer Service — Demo Data Overview</p>
  <div class="env-info">
    Environment: orgecbce8ef.crm.dynamics.com &nbsp;|&nbsp; Generated: $timestamp
  </div>
</div>

<div class="container">

  <!-- Summary Stats -->
  <div class="stats-grid">
    <div class="stat-card"><div class="number">$($d.accounts.Count)</div><div class="label">Accounts</div></div>
    <div class="stat-card"><div class="number">$($d.contacts.Count)</div><div class="label">Contacts</div></div>
    <div class="stat-card"><div class="number">$($d.products.Count)</div><div class="label">Products</div></div>
    <div class="stat-card"><div class="number">$($d.queues.Count)</div><div class="label">Queues</div></div>
    <div class="stat-card"><div class="number">$($d.cases.Count)</div><div class="label">Cases</div></div>
    <div class="stat-card"><div class="number">$($d.subjects.Count)</div><div class="label">Subjects</div></div>
    <div class="stat-card"><div class="number">$($d.slaItems.Count)</div><div class="label">SLA KPIs</div></div>
  </div>

  <!-- Accounts -->
  <div class="section">
    <div class="section-header" onclick="toggle('accounts')">
      <span class="toggle" id="toggle-accounts">&#9660;</span>
      <h2>Accounts</h2>
      <span class="count">$($d.accounts.Count)</span>
    </div>
    <div id="accounts" class="collapsible-content">
      <div class="card">
        <div class="mini-stats">
          <span class="mini-stat"><span class="num">$($mfgAccounts.Count)</span><span class="lbl">Manufacturers</span></span>
          <span class="mini-stat"><span class="num">$($distAccounts.Count)</span><span class="lbl">Distributors</span></span>
          <span class="mini-stat"><span class="num">$($euAccounts.Count)</span><span class="lbl">End Users</span></span>
        </div>
        <table>
          <thead><tr><th>Name</th><th>Type</th><th>Location</th><th>Phone</th></tr></thead>
          <tbody>$acctRows</tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Contacts -->
  <div class="section">
    <div class="section-header" onclick="toggle('contacts')">
      <span class="toggle" id="toggle-contacts">&#9660;</span>
      <h2>Contacts</h2>
      <span class="count">$($d.contacts.Count)</span>
    </div>
    <div id="contacts" class="collapsible-content">
      <div class="card">
        <div class="mini-stats">
          <span class="mini-stat"><span class="num">$($stakeContacts.Count)</span><span class="lbl">Stakeholders</span></span>
          <span class="mini-stat"><span class="num">$($distContacts.Count)</span><span class="lbl">Distributor</span></span>
          <span class="mini-stat"><span class="num">$($euContacts.Count)</span><span class="lbl">End User</span></span>
        </div>
        <table>
          <thead><tr><th>Name</th><th>Title</th><th>Account</th><th>Category</th><th>Email</th></tr></thead>
          <tbody>$contactRows</tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Products & Price Lists -->
  <div class="section">
    <div class="section-header" onclick="toggle('products')">
      <span class="toggle" id="toggle-products">&#9660;</span>
      <h2>Products</h2>
      <span class="count">$($d.products.Count)</span>
    </div>
    <div id="products" class="collapsible-content">
      <div class="two-col">
        <div class="card">
          <div class="mini-stats">
            <span class="mini-stat"><span class="num">$($zurnProducts.Count)</span><span class="lbl">Zurn / Wilkins</span></span>
            <span class="mini-stat"><span class="num">$($elkayProducts.Count)</span><span class="lbl">Elkay</span></span>
          </div>
          <table>
            <thead><tr><th>SKU</th><th>Product</th><th>Brand</th><th>Status</th></tr></thead>
            <tbody>$productRows</tbody>
          </table>
        </div>
        <div>
          <div class="card" style="margin-bottom:1rem;">
            <div style="padding:1.25rem;">
              <h3 style="font-size:1rem;color:var(--zurn-blue);margin-bottom:0.75rem;">Price Lists</h3>
              $(foreach ($pl in $d.priceLists) {
                $plState = if ($pl.statecode -eq 0) { "Active" } else { "Inactive" }
                "<div style='margin-bottom:0.5rem;'><strong>$($pl.name)</strong> <span class='badge active'>$plState</span></div>"
              })
            </div>
          </div>
          <div class="card">
            <div style="padding:1.25rem;">
              <h3 style="font-size:1rem;color:var(--zurn-blue);margin-bottom:0.75rem;">Calendar</h3>
              $(foreach ($cal in $d.calendars) {
                "<div><strong>$($cal.name)</strong></div>"
              })
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Queues -->
  <div class="section">
    <div class="section-header" onclick="toggle('queues')">
      <span class="toggle" id="toggle-queues">&#9660;</span>
      <h2>Queues</h2>
      <span class="count">$($d.queues.Count)</span>
    </div>
    <div id="queues" class="collapsible-content">
      <div class="card">
        <div class="mini-stats">
          <span class="mini-stat"><span class="num">$($zurnQueues.Count)</span><span class="lbl">Zurn</span></span>
          <span class="mini-stat"><span class="num">$($elkayQueues.Count)</span><span class="lbl">Elkay</span></span>
        </div>
        <table>
          <thead><tr><th>Queue Name</th><th>Brand</th><th>Channel</th><th>Email</th></tr></thead>
          <tbody>$queueRows</tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Subjects & SLA -->
  <div class="two-col">
    <!-- Subjects -->
    <div class="section">
      <div class="section-header" onclick="toggle('subjects')">
        <span class="toggle" id="toggle-subjects">&#9660;</span>
        <h2>Case Subjects</h2>
        <span class="count">$($d.subjects.Count)</span>
      </div>
      <div id="subjects" class="collapsible-content">
        <div class="card">
          <table>
            <thead><tr><th>Subject</th><th>Description</th></tr></thead>
            <tbody>$subjectRows</tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- SLA -->
    <div class="section">
      <div class="section-header">
        <span class="toggle">&#9660;</span>
        <h2>Service Level Agreement</h2>
      </div>
      <div class="card">
        <div class="sla-grid">
          <div class="sla-detail"><div class="label">SLA Name</div><div class="value">$slaName</div></div>
          <div class="sla-detail"><div class="label">Status</div><div class="value"><span class="badge $(if ($slaState -eq 'Active') {'active'} else {'draft'})">$slaState</span></div></div>
        </div>
        $(if ($d.slaItems.Count -gt 0) {
          "<table><thead><tr><th>KPI</th><th>Failure</th><th>Warning</th></tr></thead><tbody>$slaItemsHtml</tbody></table>"
        })
      </div>
    </div>
  </div>

  <!-- Cases -->
  <div class="section">
    <div class="section-header" onclick="toggle('cases')">
      <span class="toggle" id="toggle-cases">&#9660;</span>
      <h2>Demo Cases</h2>
      <span class="count">$($d.cases.Count)</span>
    </div>
    <div id="cases" class="collapsible-content">
      <div class="card">
        <div class="mini-stats">
          <span class="mini-stat"><span class="num">$($activeCases.Count)</span><span class="lbl">Active</span></span>
          <span class="mini-stat"><span class="num">$($resolvedCases.Count)</span><span class="lbl">Resolved</span></span>
          <span class="mini-stat"><span class="num">$p1</span><span class="lbl">High Priority</span></span>
          <span class="mini-stat"><span class="num">$p2</span><span class="lbl">Normal Priority</span></span>
          <span class="mini-stat"><span class="num">$p3</span><span class="lbl">Low Priority</span></span>
          <span class="mini-stat"><span class="num">$oEmail</span><span class="lbl">Email</span></span>
          <span class="mini-stat"><span class="num">$oPhone</span><span class="lbl">Phone</span></span>
          <span class="mini-stat"><span class="num">$oWeb</span><span class="lbl">Web</span></span>
        </div>
        <table>
          <thead><tr><th>Ticket #</th><th>Title</th><th>Priority</th><th>Origin</th><th>Status</th></tr></thead>
          <tbody>$caseRows</tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="footer">
    Zurn Elkay D365 Customer Service Demo &mdash; Data provisioned via PowerShell automation scripts
  </div>

</div>

<script>
function toggle(id) {
  const el = document.getElementById(id);
  const arrow = document.getElementById('toggle-' + id);
  el.classList.toggle('collapsed');
  if (arrow) arrow.classList.toggle('collapsed');
}
</script>

</body>
</html>
"@

$outPath = "$root\demo-data-overview.html"
$html | Out-File $outPath -Encoding utf8
Write-Host "HTML report generated: $outPath"
