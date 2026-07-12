# Script to backup artist-specific themes for performance
# This moves all artist themes to a backup folder

$themesPath = "c:\Users\Swopnil\Documents\Projects\LyricBar\themes\Artists"
$backupPath = "c:\Users\Swopnil\Documents\Projects\LyricBar\themes\Artists_BACKUP"

Write-Host "Artist Themes Backup Script" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path $backupPath) {
    Write-Host "Backup folder already exists" -ForegroundColor Yellow
    $response = Read-Host "Restore from backup instead? (y/n)"
    if ($response -eq 'y') {
        # Restore
        if (Test-Path $themesPath) {
            Remove-Item -Path $themesPath -Recurse -Force
        }
        Move-Item -Path $backupPath -Destination $themesPath
        Write-Host "✓ Artist themes restored!" -ForegroundColor Green
        exit
    }
} else {
    # Create backup
    if (Test-Path $themesPath) {
        $fileCount = (Get-ChildItem -Path $themesPath -Filter "*.py").Count
        Write-Host "Found $fileCount artist theme files" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "This will move artist themes to backup for better performance" -ForegroundColor Gray
        Write-Host "You can restore them anytime by running this script again" -ForegroundColor Gray
        Write-Host ""
        
        $response = Read-Host "Continue with backup? (y/n)"
        if ($response -eq 'y') {
            Move-Item -Path $themesPath -Destination $backupPath
            Write-Host "✓ Artist themes backed up to Artists_BACKUP/" -ForegroundColor Green
            Write-Host "✓ Performance should be improved!" -ForegroundColor Green
        } else {
            Write-Host "Cancelled" -ForegroundColor Gray
        }
    } else {
        Write-Host "Artist themes folder not found" -ForegroundColor Red
    }
}
