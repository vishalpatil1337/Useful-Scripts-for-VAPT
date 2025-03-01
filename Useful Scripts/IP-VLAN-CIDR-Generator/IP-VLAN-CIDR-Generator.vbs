' IP VLAN Generator - Final Version with Subnet Parsing Fix
' Date: February 28, 2025

Option Explicit

' Main procedure
Sub Main()
    ' Declare variables
    Dim objExcel, objWorkbook, objWorksheet
    Dim ipNetworkRange, subnetMaskRange, outputRange
    Dim ipValue, subnetValue, vlanInfo
    Dim cidrNotation
    Dim i, rowCount, startRow
    Dim outputColLetter
    Dim excelWasRunning
    Dim processedCount
    
    ' Display simplified banner
    MsgBox "IP VLAN GENERATOR" & vbNewLine & vbNewLine & _
           "- Comprehensive CIDR support (/1-/32)" & vbNewLine & _
           "- Handles complex subnet masks" & vbNewLine & _
           "- Advanced error handling", vbInformation, "IP VLAN Generator"
    
    ' Try to connect to an already running Excel instance first
    On Error Resume Next
    Set objExcel = GetObject(, "Excel.Application")
    excelWasRunning = (Err.Number = 0)
    
    ' If that fails, create a new Excel instance
    If Not excelWasRunning Then
        Set objExcel = CreateObject("Excel.Application")
        ' Ask user to open their file
        objExcel.Visible = True
        MsgBox "Please open your Excel file with the IP data, then click OK.", vbInformation, "Excel Connection"
    End If
    
    ' Ensure Excel is visible
    objExcel.Visible = True
    
    ' Try to access the active workbook
    Err.Clear
    Set objWorkbook = objExcel.ActiveWorkbook
    
    ' If no workbook is active, prompt user to open one
    If Err.Number <> 0 Or objWorkbook Is Nothing Then
        MsgBox "No active Excel workbook found. Please open your Excel file manually, then run this script again.", vbExclamation, "Error"
        If Not excelWasRunning Then
            objExcel.Quit
        End If
        Set objExcel = Nothing
        WScript.Quit
    End If
    On Error GoTo 0
    
    ' Get the active sheet
    Set objWorksheet = objWorkbook.ActiveSheet
    
    ' Display welcome message
    MsgBox "This tool will generate VLAN information with full CIDR support." & vbNewLine & vbNewLine & _
           "You will need to:" & vbNewLine & _
           "1. Select the IP Network column" & vbNewLine & _
           "2. Select the Subnet Mask column" & vbNewLine & _
           "3. Specify the output column", vbInformation, "IP VLAN Generator"
           
    ' Prompt user to select IP Network range
    MsgBox "Please select the IP Network column in your spreadsheet, then click OK.", vbInformation, "Step 1 of 3"
           
    On Error Resume Next
    Set ipNetworkRange = objExcel.Selection
    If Err.Number <> 0 Or ipNetworkRange Is Nothing Then
        MsgBox "No valid selection made. Exiting script.", vbExclamation, "Error"
        CleanupAndExit objExcel, excelWasRunning
    End If
    
    ' Prompt user to select Subnet Mask range
    MsgBox "Please select the Subnet Mask column in your spreadsheet, then click OK.", vbInformation, "Step 2 of 3"
    
    Set subnetMaskRange = objExcel.Selection
    If Err.Number <> 0 Or subnetMaskRange Is Nothing Then
        MsgBox "No valid selection made. Exiting script.", vbExclamation, "Error"
        CleanupAndExit objExcel, excelWasRunning
    End If
    On Error GoTo 0
    
    ' Validate selections
    If ipNetworkRange.Rows.Count <> subnetMaskRange.Rows.Count Then
        MsgBox "The selected ranges must have the same number of rows", vbExclamation, "Error"
        CleanupAndExit objExcel, excelWasRunning
    End If
    
    ' Ask for output column
    outputColLetter = InputBox("Enter the column letter for output (e.g., H):", "Step 3 of 3", "H")
    If outputColLetter = "" Then
        MsgBox "Operation cancelled", vbInformation, "Cancelled"
        CleanupAndExit objExcel, excelWasRunning
    End If
    
    ' Get the range for output column
    startRow = ipNetworkRange.Row
    rowCount = ipNetworkRange.Rows.Count
    Set outputRange = objWorksheet.Range(outputColLetter & startRow & ":" & outputColLetter & (startRow + rowCount - 1))
    
    ' Add visual styling to output column
    On Error Resume Next
    FormatOutputColumn outputRange, objExcel
    On Error GoTo 0
    
    ' Initialize counter for processed rows
    processedCount = 0
    
    ' Process each row
    MsgBox "Processing " & rowCount & " rows now. Please wait...", vbInformation, "Processing"
    
    For i = 1 To rowCount
        ' Get IP Network and Subnet Mask values
        ipValue = Trim(ipNetworkRange.Cells(i).Value)
        subnetValue = Trim(subnetMaskRange.Cells(i).Value)
        
        ' Skip empty rows or header rows with "IP Network" or similar text
        If ipValue = "" Or IsHeaderRow(ipValue) Then
            ' Clear the output cell (leave blank)
            outputRange.Cells(i).Value = ""
        Else
            ' Check if IP Range already contains subnet notation
            If InStr(ipValue, "/") > 0 Then
                ' IP Range already has subnet info, use it directly
                vlanInfo = ipValue
            Else
                ' Check if the subnet mask already includes CIDR notation
                If InStr(subnetValue, "/") > 0 Then
                    ' Extract CIDR directly from subnet mask if it contains it
                    cidrNotation = ExtractCIDRFromString(subnetValue)
                Else
                    ' Calculate CIDR notation from subnet mask
                    cidrNotation = GetCIDR(subnetValue)
                End If
                
                ' Generate VLAN info
                vlanInfo = ipValue & "/" & cidrNotation
            End If
            
            ' Write to output column
            outputRange.Cells(i).Value = vlanInfo
            processedCount = processedCount + 1
        End If
    Next
    
    ' Apply a filter to the header row if applicable
    On Error Resume Next
    If startRow > 1 Then
        objWorksheet.Range("A" & (startRow - 1) & ":" & outputColLetter & (startRow - 1)).AutoFilter
    End If
    On Error GoTo 0
    
    ' Complete message
    MsgBox "VLAN information generated successfully!" & vbNewLine & vbNewLine & _
           "Results:" & vbNewLine & _
           "• Rows processed: " & processedCount & vbNewLine & _
           "• Output column: " & outputColLetter, vbInformation, "Operation Complete"
    
    ' Clean up
    Set outputRange = Nothing
    Set ipNetworkRange = Nothing
    Set subnetMaskRange = Nothing
    Set objWorksheet = Nothing
    Set objWorkbook = Nothing
    
    ' Don't quit Excel if it was already running
    If Not excelWasRunning Then
        objExcel.Quit
    End If
    
    Set objExcel = Nothing
End Sub

' Extract CIDR from a string like "255.255.255.224 / 27"
Function ExtractCIDRFromString(inputString)
    Dim parts, i, part
    
    ' Default value if we can't find a valid CIDR
    ExtractCIDRFromString = 24
    
    ' Split by spaces or slashes
    parts = Split(Replace(inputString, "/", " "), " ")
    
    ' Look for a number between 1 and 32
    For i = 0 To UBound(parts)
        part = Trim(parts(i))
        If IsNumeric(part) Then
            If CInt(part) >= 1 And CInt(part) <= 32 Then
                ExtractCIDRFromString = CInt(part)
                Exit Function
            End If
        End If
    Next
End Function

' Check if this is a header row that should be skipped
Function IsHeaderRow(cellValue)
    ' Convert to lowercase for case-insensitive comparison
    Dim lowerValue
    lowerValue = LCase(cellValue)
    
    ' Check for common header text
    IsHeaderRow = False
    
    If InStr(lowerValue, "ip network") > 0 Then IsHeaderRow = True
    If InStr(lowerValue, "ip range") > 0 Then IsHeaderRow = True
    If lowerValue = "subnet" Then IsHeaderRow = True
    If lowerValue = "mask" Then IsHeaderRow = True
    If lowerValue = "vlan" Then IsHeaderRow = True
    If lowerValue = "address" Then IsHeaderRow = True
    If lowerValue = "cidr" Then IsHeaderRow = True
End Function

' Format the output column for better visibility
Sub FormatOutputColumn(outputRange, objExcel)
    On Error Resume Next
    
    ' Add borders
    outputRange.Borders.LineStyle = 1
    
    ' Add background color (light yellow)
    outputRange.Interior.Color = RGB(255, 255, 204)
    
    ' Add font formatting
    outputRange.Font.Bold = True
    
    ' Autofit column width
    outputRange.EntireColumn.AutoFit
    
    On Error GoTo 0
End Sub

' Clean up and exit
Sub CleanupAndExit(objExcel, excelWasRunning)
    If Not excelWasRunning And Not objExcel Is Nothing Then
        objExcel.Quit
    End If
    
    Set objExcel = Nothing
    WScript.Quit
End Sub

Function GetCIDR(subnetMask)
    ' Convert subnet mask to CIDR notation
    
    ' Handle special cases and common errors
    If subnetMask = "2555.255.254.0" Then
        subnetMask = "255.255.254.0"
    End If
    
    ' Extract first subnet mask if multiple are present
    If InStr(subnetMask, "/") > 0 Then
        Dim parts
        parts = Split(subnetMask, "/")
        subnetMask = Trim(parts(0))
    End If
    
    ' Quick lookup for complete CIDR range from /1 to /32
    Select Case subnetMask
        ' Class A subnet masks
        Case "128.0.0.0": GetCIDR = 1
        Case "192.0.0.0": GetCIDR = 2
        Case "224.0.0.0": GetCIDR = 3
        Case "240.0.0.0": GetCIDR = 4
        Case "248.0.0.0": GetCIDR = 5
        Case "252.0.0.0": GetCIDR = 6
        Case "254.0.0.0": GetCIDR = 7
        Case "255.0.0.0": GetCIDR = 8
        
        ' Class B subnet masks
        Case "255.128.0.0": GetCIDR = 9
        Case "255.192.0.0": GetCIDR = 10
        Case "255.224.0.0": GetCIDR = 11
        Case "255.240.0.0": GetCIDR = 12
        Case "255.248.0.0": GetCIDR = 13
        Case "255.252.0.0": GetCIDR = 14
        Case "255.254.0.0": GetCIDR = 15
        Case "255.255.0.0": GetCIDR = 16
        
        ' Class C subnet masks (most common)
        Case "255.255.128.0": GetCIDR = 17
        Case "255.255.192.0": GetCIDR = 18
        Case "255.255.224.0": GetCIDR = 19
        Case "255.255.240.0": GetCIDR = 20
        Case "255.255.248.0": GetCIDR = 21
        Case "255.255.252.0": GetCIDR = 22
        Case "255.255.254.0": GetCIDR = 23
        Case "255.255.255.0": GetCIDR = 24
        
        ' Smaller subnets
        Case "255.255.255.128": GetCIDR = 25
        Case "255.255.255.192": GetCIDR = 26
        Case "255.255.255.224": GetCIDR = 27
        Case "255.255.255.240": GetCIDR = 28
        Case "255.255.255.248": GetCIDR = 29
        Case "255.255.255.252": GetCIDR = 30
        Case "255.255.255.254": GetCIDR = 31
        Case "255.255.255.255": GetCIDR = 32
        
        ' If not in the quick lookup, calculate it
        Case Else: GetCIDR = CalculateCIDRFromMask(subnetMask)
    End Select
End Function

Function CalculateCIDRFromMask(subnetMask)
    ' Calculate CIDR from subnet mask when not found in lookup table
    Dim octets, octet, binary, i, count
    
    ' Split the subnet mask into octets
    octets = Split(subnetMask, ".")
    
    ' Initialize count of consecutive 1s
    count = 0
    
    ' Process each octet
    For i = 0 To UBound(octets)
        If IsNumeric(octets(i)) Then
            octet = CInt(octets(i))
            
            ' Convert to binary and count 1s
            binary = ConvertToBinary(octet)
            count = count + CountOnes(binary)
        End If
    Next
    
    ' Default to /24 if calculation failed
    If count = 0 Then count = 24
    
    CalculateCIDRFromMask = count
End Function

Function ConvertToBinary(decimalValue)
    ' Convert decimal to binary
    Dim binary, i
    
    binary = ""
    For i = 7 To 0 Step -1
        If decimalValue And (2 ^ i) Then
            binary = binary & "1"
        Else
            binary = binary & "0"
        End If
    Next
    
    ConvertToBinary = binary
End Function

Function CountOnes(binaryString)
    ' Count 1s in a binary string
    Dim count, i
    
    count = 0
    For i = 1 To Len(binaryString)
        If Mid(binaryString, i, 1) = "1" Then
            count = count + 1
        End If
    Next
    
    CountOnes = count
End Function

Function RGB(Red, Green, Blue)
    ' VBScript compatible RGB function
    RGB = Red + (Green * 256) + (Blue * 65536)
End Function

' Run the main procedure
Main()