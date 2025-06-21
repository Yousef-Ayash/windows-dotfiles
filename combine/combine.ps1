$outputFile = "combined_output.txt"
$baseDir = Get-Location

# Create or overwrite the output file
Set-Content -Path $outputFile -Value "" -Encoding UTF8

# Get all files recursively
Get-ChildItem -Path $baseDir -Recurse -File | ForEach-Object {
    $file = $_
    $relPath = $file.FullName.Substring($baseDir.Path.Length + 1)

    # Skip the output file itself
    if ($file.Name -eq $outputFile) {
        return
    }

    try {
        $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
        Add-Content -Path $outputFile -Value "<-- $relPath -->"
        Add-Content -Path $outputFile -Value $content
        Add-Content -Path $outputFile -Value "`r`n"
    }
    catch {
        Write-Host "Skipped $($file.FullName): $_"
    }
}