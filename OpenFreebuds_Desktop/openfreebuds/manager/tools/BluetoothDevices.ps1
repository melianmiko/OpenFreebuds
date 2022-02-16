Add-Type -AssemblyName System.Runtime.WindowsRuntime

[Windows.Devices.Enumeration.DeviceInformation,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
[Windows.Devices.Bluetooth.BluetoothDevice,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

$selector = [Windows.Devices.Bluetooth.BluetoothDevice]::GetDeviceSelectorFromPairingState($true)
$devices = Await ([Windows.Devices.Enumeration.DeviceInformation]::findAllAsync($selector)) ([Windows.Devices.Enumeration.DeviceInformationCollection])

ForEach-Object -InputObject $devices -Process {
    $id = $PSItem.Id
    $bt = Await ([Windows.Devices.Bluetooth.BluetoothDevice]::FromIdAsync($id)) ([Windows.Devices.Bluetooth.BluetoothDevice])

    $connected = $bt.ConnectionStatus -eq "Connected"
    $name = $bt.Name
    $address = $bt.HostName.RawName.Substring(1, $bt.HostName.RawName.Length-2)

    echo "$($name);$($address);$($connected)"
}

