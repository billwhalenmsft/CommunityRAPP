<#
.SYNOPSIS
    Dataverse Helper Module for D365 Customer Service Demo Setup
.DESCRIPTION
    Provides reusable functions for authenticating and interacting with
    Dataverse Web API via pac CLI token acquisition.
#>

# ============================================================
# Configuration
# ============================================================
$script:DataverseBaseUrl = "https://orgecbce8ef.crm.dynamics.com"
$script:ApiVersion = "v9.2"
$script:ApiUrl = "$($script:DataverseBaseUrl)/api/data/$($script:ApiVersion)"
$script:AuthToken = $null

function Connect-Dataverse {
    <#
    .SYNOPSIS
        Authenticates to Dataverse using pac CLI and caches the token.
    #>
    [CmdletBinding()]
    param()

    Write-Host "Authenticating to Dataverse..." -ForegroundColor Cyan

    # Suppress errors from native CLI commands
    $oldEAP = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"

    # Get token via az CLI (pac CLI skipped - hangs in non-interactive terminals)
    $token = & az account get-access-token --resource $script:DataverseBaseUrl --query accessToken -o tsv 2>$null
    if (-not $token) {
        $token = & az account get-access-token --resource "$($script:DataverseBaseUrl)/" --query accessToken -o tsv 2>$null
    }
    if (-not $token) {
        $token = & az account get-access-token --resource "https://orgecbce8ef.crm.dynamics.com" --query accessToken -o tsv 2>$null
    }

    $ErrorActionPreference = $oldEAP

    if ($token) {
        $script:AuthToken = $token
        Write-Host "Authenticated successfully to $($script:DataverseBaseUrl)" -ForegroundColor Green
    } else {
        throw "Could not obtain Dataverse access token. Ensure 'az login' is completed and you have access to $($script:DataverseBaseUrl)."
    }
}

function Get-DataverseHeaders {
    <#
    .SYNOPSIS
        Returns standard Dataverse API request headers with auth token.
    #>
    if (-not $script:AuthToken) {
        Connect-Dataverse
    }
    return @{
        "Authorization"    = "Bearer $($script:AuthToken)"
        "OData-MaxVersion" = "4.0"
        "OData-Version"    = "4.0"
        "Accept"           = "application/json"
        "Content-Type"     = "application/json; charset=utf-8"
        "Prefer"           = "return=representation"
    }
}

function Invoke-DataverseGet {
    <#
    .SYNOPSIS
        Performs a GET request against the Dataverse Web API.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$EntitySet,

        [string]$Filter,
        [string]$Select,
        [string]$Expand,
        [int]$Top = 0
    )

    $headers = Get-DataverseHeaders
    $url = "$($script:ApiUrl)/$EntitySet"

    $queryParams = @()
    if ($Filter) { $queryParams += "`$filter=" + [System.Uri]::EscapeDataString($Filter) }
    if ($Select) { $queryParams += "`$select=$Select" }
    if ($Expand) { $queryParams += "`$expand=$Expand" }
    if ($Top -gt 0) { $queryParams += "`$top=$Top" }

    if ($queryParams.Count -gt 0) {
        $url += "?" + ($queryParams -join "&")
    }

    try {
        $response = Invoke-RestMethod -Uri $url -Method Get -Headers $headers -ErrorAction Stop
        # Use comma operator to prevent PS 5.1 pipeline from unwrapping single-element arrays
        if ($null -ne $response.value) {
            return , $response.value
        }
        return , @()
    } catch {
        Write-Error "GET $url failed: $($_.Exception.Message)"
        if ($_.ErrorDetails.Message) {
            Write-Error $_.ErrorDetails.Message
        }
        return $null
    }
}

function Invoke-DataversePost {
    <#
    .SYNOPSIS
        Creates a record in Dataverse via POST.
    .OUTPUTS
        The created record ID (GUID) extracted from OData-EntityId header, or $null on failure.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$EntitySet,

        [Parameter(Mandatory)]
        [hashtable]$Body
    )

    $headers = Get-DataverseHeaders
    $url = "$($script:ApiUrl)/$EntitySet"
    $jsonBody = $Body | ConvertTo-Json -Depth 10

    try {
        $response = Invoke-WebRequest -Uri $url -Method Post -Headers $headers -Body $jsonBody -UseBasicParsing -ErrorAction Stop
        
        # Try parsing the response body first (if Prefer: return=representation is set)
        if ($response.Content) {
            $parsed = $response.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
            if ($parsed) { return $parsed }
        }
        
        # Fallback: Extract record ID from OData-EntityId header
        $entityId = $response.Headers["OData-EntityId"]
        if ($entityId) {
            if ($entityId -match '\(([0-9a-fA-F\-]{36})\)') {
                return $Matches[1]
            }
        }
        return $true  # Indicate success even if no ID returned (e.g. unbound actions)
    } catch {
        Write-Error "POST $url failed: $($_.Exception.Message)"
        if ($_.ErrorDetails.Message) {
            $errDetail = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
            if ($errDetail.error.message) {
                Write-Error "Dataverse Error: $($errDetail.error.message)"
            } else {
                Write-Error $_.ErrorDetails.Message
            }
        }
        return $null
    }
}

function Invoke-DataversePatch {
    <#
    .SYNOPSIS
        Updates a record in Dataverse via PATCH.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$EntitySet,

        [Parameter(Mandatory)]
        [guid]$RecordId,

        [Parameter(Mandatory)]
        [hashtable]$Body
    )

    $headers = Get-DataverseHeaders
    $url = "$($script:ApiUrl)/$EntitySet($RecordId)"
    $jsonBody = $Body | ConvertTo-Json -Depth 10

    try {
        Invoke-RestMethod -Uri $url -Method Patch -Headers $headers -Body $jsonBody -ErrorAction Stop
        return $true
    } catch {
        Write-Error "PATCH $url failed: $($_.Exception.Message)"
        if ($_.ErrorDetails.Message) {
            Write-Error $_.ErrorDetails.Message
        }
        return $false
    }
}

function Invoke-DataverseDelete {
    <#
    .SYNOPSIS
        Deletes a record in Dataverse.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$EntitySet,

        [Parameter(Mandatory)]
        [guid]$RecordId
    )

    $headers = Get-DataverseHeaders
    $url = "$($script:ApiUrl)/$EntitySet($RecordId)"

    try {
        Invoke-RestMethod -Uri $url -Method Delete -Headers $headers -ErrorAction Stop
        return $true
    } catch {
        Write-Error "DELETE $url failed: $($_.Exception.Message)"
        return $false
    }
}

function Find-OrCreate-Record {
    <#
    .SYNOPSIS
        Finds an existing record by filter or creates a new one. Returns the record ID.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$EntitySet,

        [Parameter(Mandatory)]
        [string]$Filter,

        [Parameter(Mandatory)]
        [string]$IdField,

        [Parameter(Mandatory)]
        [hashtable]$Body,

        [string]$DisplayName = ""
    )

    $existing = Invoke-DataverseGet -EntitySet $EntitySet -Filter $Filter -Select $IdField -Top 1
    if ($existing -and $existing.Count -gt 0) {
        $id = $existing[0].$IdField
        Write-Host "  Found existing: $DisplayName ($id)" -ForegroundColor DarkGray
        return [guid]$id
    }

    Write-Host "  Creating: $DisplayName" -ForegroundColor Green
    $result = Invoke-DataversePost -EntitySet $EntitySet -Body $Body
    if ($result) {
        # Result may be a full object (Prefer: return=representation) or a GUID string
        if ($result.$IdField) {
            return [guid]$result.$IdField
        }
        try { return [guid]$result } catch {}
    }
    
    # Fallback: fetch the newly created record
    $created = @(Invoke-DataverseGet -EntitySet $EntitySet -Filter $Filter -Select $IdField -Top 1)
    if ($created -and $created.Count -gt 0 -and $created[0]) {
        return [guid]$created[0].$IdField
    }

    Write-Warning "Could not confirm creation of $DisplayName"
    return $null
}

function Write-StepHeader {
    param([string]$StepNumber, [string]$Title)
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host " Step $StepNumber : $Title" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host ""
}

function Get-DataverseApiUrl {
    <#
    .SYNOPSIS
        Returns the Dataverse API base URL for use in custom API calls.
    #>
    return $script:ApiUrl
}

Export-ModuleMember -Function @(
    'Connect-Dataverse',
    'Get-DataverseHeaders',
    'Get-DataverseApiUrl',
    'Invoke-DataverseGet',
    'Invoke-DataversePost',
    'Invoke-DataversePatch',
    'Invoke-DataverseDelete',
    'Find-OrCreate-Record',
    'Write-StepHeader'
)
