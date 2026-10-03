Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$out = Join-Path $PSScriptRoot "..\.scratch-anki\clipboard-shot.png"
$img = [System.Windows.Forms.Clipboard]::GetImage()
if ($img) {
    $resolved = [System.IO.Path]::GetFullPath($out)
    $img.Save($resolved, [System.Drawing.Imaging.ImageFormat]::Png)
    Write-Output "saved: $resolved"
} else {
    Write-Output "no image in clipboard"
    $t = [System.Windows.Forms.Clipboard]::GetText()
    if ($t) { Write-Output "--- text ---"; Write-Output $t }
}
