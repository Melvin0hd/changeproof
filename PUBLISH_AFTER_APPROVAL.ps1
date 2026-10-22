param(
    [ValidateSet('Plan','Source','Hosting')][string]$Stage = 'Plan',
    [switch]$Execute,
    [string]$Approval,
    [string]$ApprovedCommit,
    [string]$ApprovedManifestSha256
)
$ErrorActionPreference = 'Stop'
$repo = 'Melvin0hd/changeproof'
$root = $PSScriptRoot
if (-not $Execute -or $Stage -eq 'Plan') {
    Write-Output 'PLAN ONLY: no network writes.'
    Write-Output 'Source: verify approved hashes/account/absent target, create only Melvin0hd/changeproof public, push clean HEAD to main.'
    Write-Output 'Hosting: separately approve Pages, enable workflow publication, dispatch ONE manual Pages workflow including offline validation.'
    Write-Output 'No provider calls, billing changes, video upload or Devpost submission.'
    exit 0
}
if ($ApprovedCommit -notmatch '^[0-9a-f]{40}$' -or $ApprovedManifestSha256 -notmatch '^[0-9a-f]{64}$') {
    throw 'Exact approved commit and manifest hash are required. No write performed.'
}
$expectedApproval = if ($Stage -eq 'Source') { 'AUTHORIZE_CHANGEPROOF_PUBLIC_SOURCE' } else { 'AUTHORIZE_CHANGEPROOF_PAGES' }
if ($Approval -cne $expectedApproval) { throw 'Missing stage-specific publication approval. No write performed.' }
function Git-Checked([string[]]$GitArgs) {
    $result = & git -C $root @GitArgs
    if ($LASTEXITCODE -ne 0) { throw 'Git operation failed. No automatic retry.' }
    return $result
}
if ((Git-Checked @('rev-parse','HEAD')) -cne $ApprovedCommit) { throw 'Approved commit mismatch.' }
if (Git-Checked @('status','--porcelain')) { throw 'Working tree is not clean.' }
$manifest = Join-Path $root 'RELEASE_MANIFEST.json'
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $manifest).Hash.ToLowerInvariant() -cne $ApprovedManifestSha256) {
    throw 'Approved manifest hash mismatch.'
}
$files = (Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json).files
foreach ($property in $files.PSObject.Properties) {
    $path = Join-Path $root $property.Name
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant() -cne $property.Value) { throw 'Source hash mismatch.' }
}
$gh = (Get-Command gh -ErrorAction Stop).Source
function Gh-Checked([string[]]$GhArgs) {
    $result = & $gh @GhArgs
    if ($LASTEXITCODE -ne 0) { throw 'GitHub operation failed. No automatic retry or alternate credentials.' }
    return $result
}
$login = Gh-Checked @('api','user','--jq','.login')
if ($login -cne 'Melvin0hd') { throw 'Wrong authenticated GitHub account. No write performed.' }
if ($Stage -eq 'Source') {
    $probe = & $gh api "repos/$repo" --silent 2>&1
    if ($LASTEXITCODE -eq 0) { throw 'Target already exists. Stop for owner review; do not overwrite it.' }
    if (($probe | Out-String) -notmatch '404') { throw 'Destination access failed for a reason other than 404. Stop.' }
    Gh-Checked @('repo','create',$repo,'--public','--description','Source-linked decision review with bounded Tavily and Nemotron extraction','--disable-wiki')
    $info = Gh-Checked @('api',"repos/$repo",'--jq','{full_name,private,permissions}') | ConvertFrom-Json
    if ($info.full_name -cne $repo -or $info.private -or -not $info.permissions.push) { throw 'Public owner/write verification failed. Stop after partial creation.' }
    $hooks = Join-Path $root '.git/release-empty-hooks'
    New-Item -ItemType Directory -Path $hooks -Force | Out-Null
    $helper = '!"' + ($gh -replace '\\','/') + '" auth git-credential'
    Git-Checked @('-c',"core.hooksPath=$hooks",'-c','credential.helper=','-c',"credential.helper=$helper",'push',"https://github.com/$repo.git",'HEAD:refs/heads/main')
    Gh-Checked @('repo','edit',$repo,'--default-branch','main')
    Write-Output 'Source published. Hosting remains a separate approval. No workflow automatically triggered.'
} else {
    $info = Gh-Checked @('api',"repos/$repo",'--jq','{full_name,private,permissions}') | ConvertFrom-Json
    if ($info.full_name -cne $repo -or $info.private -or -not $info.permissions.admin) { throw 'Expected public repository/admin access not verified.' }
    $remoteHead = Gh-Checked @('api',"repos/$repo/commits/main",'--jq','.sha')
    if ($remoteHead -cne $ApprovedCommit) { throw 'Public main is not the approved source commit.' }
    $probe = & $gh api "repos/$repo/pages" --silent 2>&1
    if ($LASTEXITCODE -ne 0) {
        if (($probe | Out-String) -notmatch '404') { throw 'Pages access failed. Stop.' }
        Gh-Checked @('api',"repos/$repo/pages",'--method','POST','-f','build_type=workflow')
    } else {
        $buildType = Gh-Checked @('api',"repos/$repo/pages",'--jq','.build_type')
        if ($buildType -cne 'workflow') { throw 'Existing Pages configuration is unexpected. Stop instead of replacing it.' }
    }
    Gh-Checked @('workflow','run','pages.yml','--repo',$repo,'--ref','main','-f','approval=APPROVE_CHANGEPROOF_PUBLIC_DEMO')
    Write-Output 'Exactly one Pages workflow dispatched. Inspect its actual result before claiming publication success. No automatic redispatch.'
}
