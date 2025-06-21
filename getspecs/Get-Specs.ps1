# Set output path
$desktopPath = [System.Environment]::GetFolderPath("Desktop")
$outputPath = Join-Path $desktopPath "specs.txt"

# Get PC Name
$pcName = $env:COMPUTERNAME

# Username
$username = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

# Windows Version
$osInfo = Get-CimInstance Win32_OperatingSystem
$OSArchitecture = $osInfo.CimInstanceProperties | Where-Object {
	$_.Name -eq "OSArchitecture"
}
$windowsVersion = "$($osInfo.Caption) [$($OSArchitecture.Value)]"

# Get CPU Info
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1 -Property Name

# Get RAM Info
$ram = Get-CimInstance Win32_PhysicalMemory
$totalRamGB = [math]::Round(($ram | Measure-Object -Property Capacity -Sum).Sum / 1GB, 2)

# Get GPU Info
$gpu = Get-CimInstance Win32_VideoController | Select-Object -First 1 -Property Name

# Get Storage Info
$disks = Get-PhysicalDisk | Select-Object MediaType, Size, FriendlyName
$diskInfo = $disks | ForEach-Object {
	[PSCustomObject]@{
		Name      = $_.FriendlyName
		SizeGB    = [math]::Round($_.Size / 1GB, 2)
		MediaType = $_.MediaType
	}
}

# Keyboard and Mouse Port type
$inputDevices = Get-PnpDevice -Class Keyboard, Mouse | Where-Object { $_.Status -eq "OK" }
$keyboardType = "Unavailable"
$mouseType = "Unavailable"

foreach ($device in $inputDevices) {
	if ($device.Class -eq "Keyboard") {
		if ($device.InstanceId -like "*HID*") {
			$keyboardType = "USB"
		}
		elseif ($device.InstanceId -like "*ACPI*") {
			$keyboardType = "PS/2"
		}
	}
	if ($device.Class -eq "Mouse") {
		if ($device.InstanceId -like "*HID*") {
			$mouseType = "USB"
		}
		elseif ($device.InstanceId -like "*ACPI*") {
			$mouseType = "PS/2"
		}
	}
}

# Printers
$printers = Get-CimInstance Win32_Printer | Where-Object {
	$_.WorkOffline -eq $false -and $_.DetectedErrorState -eq $null -and $_.PortName -match "^USB|^LPT|^COM"
} | Select-Object Name, PortName, Default

# Scanners
$scanner = Get-PnpDevice -Class "Image" | Where-Object { $_.Status -eq "OK" }

# Network ???
$ips = Get-NetIPAddress | Where-Object {
	$_.InterfaceAlias -match "^Wi-Fi|^Local area connection" -and $_.AddressState -eq "Preferred"
}

# Get Screen Size if availabe (approximation)
function Get-ScreenSize {
	try {
		$monitors = Get-WmiObject -Namespace root\wmi -Class WmiMonitorDescriptorMethods
		foreach ($monitor in $monitors) {
			$descriptor = $monitor.GetMonitorDescriptor(0).MonitorDescriptor
			if ($descriptor.Length -ge 23) {
				$horizontalSize = $edid[21] # cm
				$verticalSize = $edid[22] # cm
				if ($horizontalSize -and $verticalSize) {
					$horizontalInches = $horizontalSize * 0.3937
					$verticalInches = $verticalSize * 0.3937
					$inches = [math]::Round([math]::Sqrt([math]::Pow($horizontalInches, 2) + [math]::Pow($verticalInches, 2)), 1)
					return $inches
				}
			}
		}
	}
 catch {
		return "Unavailable"
	}
}
$screenSize = Get-ScreenSize

# Get monitor info
$monitorInfo = Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorId | ForEach-Object {
	$manufacturer = ($_.ManufacturerName | ForEach-Object { [char] $_ }) -join ''
	$productName = ($_.UserFriendlyName | ForEach-Object { [char] $_ }) -join ''
	[PSCustomObject]@{
		Manufacturer = $manufacturer
		ProductName  = $productName
	}
}

# Prepare Output Content
$output = @()
$output += "===== PC Specifications ====="
$output += "PC Name: $pcName"
$output += "Username: $username"
$output += "Windows Version: $windowsVersion"
$output += "CPU: $($cpu.Name)"
$output += "RAM: $totalRamGB GB"
$output += "GPU: $($gpu.Name)"
$output += "Keyboard Type: $keyboardType"
$output += "Mouse Type: $mouseType"
if ($screenSize -notmatch "Unavailable") {
	$output += "Screen Size: $screenSize inches"
}
else {
	$output += "Screen Size: Unavailable"
}
if ($monitorInfo) {
	foreach ($monitor in $monitorInfo) {
		$output += "Monitor: $($monitor.Manufacturer) - $($monitor.ProductName)"
	}
}
else {
	$output += "Monitor: Unavailable"
}
# $output += ""
$output += "Printers:"
if ($printers) {
	foreach ($printer in $printers) {
		$isDefault = if ($printer.Default) { "Deafult" } else { "" }
		$output += " -  $($printer.Name) on $($printer.PortName) $isDefault"
	}
}
else {
	$output += " - No active physical printers found."
}
# $output += ""
$output += "Scanners:"
if ($scanners) {
	foreach ($scanner in $scanners) {
		$output += " - $($scanner.FriendlyName)"
	}
}
else {
	$output += " - Non Found"
}
$output += ""
$output += "IP:"
foreach ($ip in $ips) {
	$output += " - $($ip.InterfaceAlias): $($ip.IPAddress)"
}
$output += ""
$output += "Storage Devices:"
$output += "-----------------------------------------------"
$diskInfo | ForEach-Object {
	$output += "Name: $($_.Name)`nSize: $($_.SizeGB) GB`nType: $($_.MediaType)`n"
}

# Export to file
$output | Out-File -FilePath $outputPath -Encoding utf8 -Force

Write-Host "Specs exported to: $outputpath"

