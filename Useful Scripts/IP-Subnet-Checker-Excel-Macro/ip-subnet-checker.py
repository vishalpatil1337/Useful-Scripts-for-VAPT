Option Explicit

' Change approach to avoid user-defined type issues
' Instead of using a custom type, we'll use dictionaries with string keys

' Function to check if an IP is in a subnet using bitwise operations
Function IsIPInSubnet(ipAddress As String, subnetWithMask As String, ipCache As Object, subnetCache As Object) As Boolean
    Dim pos As Integer
    Dim subnet As String
    Dim maskBits As Integer
    Dim ipBinary As String
    Dim subnetBinary As String
    
    ' Use cached values if available
    ' ipCache structure:
    ' ipCache("ip_address_valid") = True/False
    ' ipCache("ip_address_binary") = binary string
    
    Dim ipValidKey As String, ipBinaryKey As String
    Dim subnetValidKey As String, subnetBinaryKey As String
    
    ipValidKey = ipAddress & "_valid"
    ipBinaryKey = ipAddress & "_binary"
    
    If Not ipCache.Exists(ipValidKey) Then
        ipCache(ipValidKey) = IsValidIP(ipAddress)
        If ipCache(ipValidKey) Then
            ipCache(ipBinaryKey) = IPToBinary(ipAddress)
        Else
            ipCache(ipBinaryKey) = ""
        End If
    End If
    
    If Not ipCache(ipValidKey) Then
        IsIPInSubnet = False
        Exit Function
    End If
    
    subnetValidKey = subnetWithMask & "_valid"
    subnetBinaryKey = subnetWithMask & "_binary"
    
    If Not subnetCache.Exists(subnetValidKey) Then
        subnetCache(subnetValidKey) = IsValidSubnet(subnetWithMask)
        If subnetCache(subnetValidKey) Then
            ' Extract subnet and mask
            pos = InStr(subnetWithMask, "/")
            subnet = Left(subnetWithMask, pos - 1)
            subnetCache(subnetBinaryKey) = IPToBinary(subnet)
        Else
            subnetCache(subnetBinaryKey) = ""
        End If
    End If
    
    If Not subnetCache(subnetValidKey) Then
        IsIPInSubnet = False
        Exit Function
    End If
    
    ' Get binary representations
    ipBinary = ipCache(ipBinaryKey)
    subnetBinary = subnetCache(subnetBinaryKey)
    
    ' Extract mask bits
    pos = InStr(subnetWithMask, "/")
    maskBits = CInt(Mid(subnetWithMask, pos + 1))
    
    ' Compare the first maskBits bits
    Dim ipNetworkPortion As String
    Dim subnetNetworkPortion As String
    
    ipNetworkPortion = Left(ipBinary, maskBits)
    subnetNetworkPortion = Left(subnetBinary, maskBits)
    
    IsIPInSubnet = (ipNetworkPortion = subnetNetworkPortion)
End Function

' Function to convert IP to binary efficiently
Function IPToBinary(ipAddress As String) As String
    Dim ipOctets() As String
    Dim result As String
    Dim i As Integer
    
    ' Convert IP to binary
    ipOctets = Split(ipAddress, ".")
    result = ""
    
    For i = 0 To 3
        result = result & DecToBin(CInt(ipOctets(i)))
    Next i
    
    IPToBinary = result
End Function

' Function to convert decimal to 8-bit binary (optimized)
Function DecToBin(decimalNum As Integer) As String
    Dim result As String
    Dim i As Integer
    
    result = ""
    For i = 7 To 0 Step -1
        If (decimalNum And (2 ^ i)) > 0 Then
            result = result & "1"
        Else
            result = result & "0"
        End If
    Next i
    
    DecToBin = result
End Function

' Function to validate IP address format
Function IsValidIP(ipAddress As String) As Boolean
    Dim regex As Object
    Static regexIP As Object
    
    ' Use static regex object for better performance
    If regexIP Is Nothing Then
        Set regexIP = CreateObject("VBScript.RegExp")
        With regexIP
            .Pattern = "^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
            .Global = True
        End With
    End If
    
    IsValidIP = regexIP.Test(ipAddress)
End Function

' Function to validate subnet format (IP/mask)
Function IsValidSubnet(subnet As String) As Boolean
    Static regexSubnet As Object
    Dim parts() As String
    Dim maskBits As Integer
    
    ' Use static regex object for better performance
    If regexSubnet Is Nothing Then
        Set regexSubnet = CreateObject("VBScript.RegExp")
        With regexSubnet
            .Pattern = "^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/([0-9]|[1-2][0-9]|3[0-2])$"
            .Global = True
        End With
    End If
    
    If Not regexSubnet.Test(subnet) Then
        IsValidSubnet = False
        Exit Function
    End If
    
    ' Extract mask bits to validate
    parts = Split(subnet, "/")
    maskBits = CInt(parts(1))
    
    If maskBits < 0 Or maskBits > 32 Then
        IsValidSubnet = False
        Exit Function
    End If
    
    IsValidSubnet = True
End Function

' Main subroutine that runs the IP/Subnet checker
Sub CheckIPsInSubnets()
    Dim ws As Worksheet
    Dim resultSheet As Worksheet
    Dim ipRange As Range
    Dim subnetRange As Range
    Dim i As Long, j As Long
    Dim ip As String, subnet As String
    Dim resultsRow As Long
    Dim unmatchedIPs() As String
    Dim unmatchedSubnets() As String
    Dim unmatchedIPCount As Long
    Dim unmatchedSubnetCount As Long
    Dim isMatch As Boolean
    Dim matchFound As Boolean
    Dim subnetMatches() As Boolean
    Dim startTime As Double
    Dim ipCache As Object
    Dim subnetCache As Object
    
    ' Start timing
    startTime = Timer
    
    ' Create dictionaries for caching
    Set ipCache = CreateObject("Scripting.Dictionary")
    Set subnetCache = CreateObject("Scripting.Dictionary")
    
    ' Get the active worksheet
    Set ws = ActiveSheet
    
    ' Let user select IP range
    On Error Resume Next
    Set ipRange = Application.InputBox("Select the range containing IP addresses:", "Select IP Range", Type:=8)
    On Error GoTo 0
    
    If ipRange Is Nothing Then
        MsgBox "Operation cancelled.", vbInformation
        Exit Sub
    End If
    
    ' Let user select Subnet range
    On Error Resume Next
    Set subnetRange = Application.InputBox("Select the range containing subnet addresses:", "Select Subnet Range", Type:=8)
    On Error GoTo 0
    
    If subnetRange Is Nothing Then
        MsgBox "Operation cancelled.", vbInformation
        Exit Sub
    End If
    
    ' Initialize arrays for unmatched IPs and subnets
    ReDim unmatchedIPs(1 To ipRange.Cells.Count)
    ReDim unmatchedSubnets(1 To subnetRange.Cells.Count)
    unmatchedIPCount = 0
    unmatchedSubnetCount = 0
    
    ' Create results sheet
    On Error Resume Next
    Set resultSheet = Worksheets("IP_Subnet_Results")
    If Err.Number <> 0 Then
        Set resultSheet = Worksheets.Add(After:=Worksheets(Worksheets.Count))
        resultSheet.Name = "IP_Subnet_Results"
    End If
    On Error GoTo 0
    
    ' Clear previous results
    resultSheet.Cells.Clear
    
    ' Set up headers
    resultSheet.Cells(1, 1).Value = "IP Address"
    resultSheet.Cells(1, 2).Value = "Matching Subnet"
    resultSheet.Cells(1, 3).Value = "Status"
    resultSheet.Range("A1:C1").Font.Bold = True
    
    ' Track which subnets have matches
    ReDim subnetMatches(1 To subnetRange.Cells.Count)
    
    ' Process each IP
    resultsRow = 2
    
    ' Pre-load all IPs and subnets into memory
    Dim ipArray() As String
    Dim subnetArray() As String
    ReDim ipArray(1 To ipRange.Cells.Count)
    ReDim subnetArray(1 To subnetRange.Cells.Count)
    
    For i = 1 To ipRange.Cells.Count
        ipArray(i) = ipRange.Cells(i).Value
    Next i
    
    For j = 1 To subnetRange.Cells.Count
        subnetArray(j) = subnetRange.Cells(j).Value
    Next j
    
    ' Process each IP
    For i = 1 To ipRange.Cells.Count
        ip = ipArray(i)
        
        ' Skip empty cells
        If ip <> "" Then
            matchFound = False
            
            ' Check against each subnet
            For j = 1 To subnetRange.Cells.Count
                subnet = subnetArray(j)
                
                ' Skip empty cells
                If subnet <> "" Then
                    If IsIPInSubnet(ip, subnet, ipCache, subnetCache) Then
                        resultSheet.Cells(resultsRow, 1).Value = ip
                        resultSheet.Cells(resultsRow, 2).Value = subnet
                        resultSheet.Cells(resultsRow, 3).Value = "Match"
                        resultsRow = resultsRow + 1
                        matchFound = True
                        subnetMatches(j) = True
                    End If
                End If
            Next j
            
            ' If no match found, add to unmatched IPs
            If Not matchFound Then
                unmatchedIPCount = unmatchedIPCount + 1
                unmatchedIPs(unmatchedIPCount) = ip
            End If
        End If
    Next i
    
    ' Find unmatched subnets
    For j = 1 To subnetRange.Cells.Count
        If Not subnetMatches(j) Then
            subnet = subnetArray(j)
            If subnet <> "" Then
                unmatchedSubnetCount = unmatchedSubnetCount + 1
                unmatchedSubnets(unmatchedSubnetCount) = subnet
            End If
        End If
    Next j
    
    ' Add unmatched IPs to results
    If unmatchedIPCount > 0 Then
        resultSheet.Cells(resultsRow, 1).Value = "UNMATCHED IPs"
        resultSheet.Cells(resultsRow, 1).Font.Bold = True
        resultsRow = resultsRow + 1
        
        For i = 1 To unmatchedIPCount
            resultSheet.Cells(resultsRow, 1).Value = unmatchedIPs(i)
            resultSheet.Cells(resultsRow, 3).Value = "No matching subnet"
            resultSheet.Cells(resultsRow, 3).Font.Color = RGB(192, 0, 0)
            resultsRow = resultsRow + 1
        Next i
    End If
    
    ' Add unmatched subnets to results
    If unmatchedSubnetCount > 0 Then
        resultSheet.Cells(resultsRow, 1).Value = "UNMATCHED SUBNETS"
        resultSheet.Cells(resultsRow, 1).Font.Bold = True
        resultsRow = resultsRow + 1
        
        For i = 1 To unmatchedSubnetCount
            resultSheet.Cells(resultsRow, 2).Value = unmatchedSubnets(i)
            resultSheet.Cells(resultsRow, 3).Value = "No matching IPs"
            resultSheet.Cells(resultsRow, 3).Font.Color = RGB(192, 0, 0)
            resultsRow = resultsRow + 1
        Next i
    End If
    
    ' Format results
    resultSheet.Columns("A:C").AutoFit
    
    ' Add simple formatting
    With resultSheet.Range("A1").CurrentRegion
        .Borders.LineStyle = xlContinuous
        .Borders.Weight = xlThin
    End With
    
    ' Apply color coding
    For i = 2 To resultsRow - 1
        If resultSheet.Cells(i, 3).Value = "Match" Then
            resultSheet.Cells(i, 3).Font.Color = RGB(0, 128, 0)
        End If
    Next i
    
    ' Activate the results sheet
    resultSheet.Activate
    resultSheet.Cells(1, 1).Select
    
    ' Display summary with performance information
    MsgBox "Analysis complete!" & vbCrLf & vbCrLf & _
           "Total IPs analyzed: " & ipRange.Cells.Count & vbCrLf & _
           "Total subnets analyzed: " & subnetRange.Cells.Count & vbCrLf & _
           "Unmatched IPs: " & unmatchedIPCount & vbCrLf & _
           "Unmatched subnets: " & unmatchedSubnetCount & vbCrLf & _
           "Processing time: " & Format(Timer - startTime, "0.00") & " seconds", _
           vbInformation, "IP Subnet Analysis"
End Sub

' Custom function to use in worksheet formulas
Function IsInSubnet(ipAddress As String, subnetWithMask As String) As String
    Static ipCache As Object
    Static subnetCache As Object
    
    ' Initialize caches if needed
    If ipCache Is Nothing Then
        Set ipCache = CreateObject("Scripting.Dictionary")
        Set subnetCache = CreateObject("Scripting.Dictionary")
    End If
    
    If IsIPInSubnet(ipAddress, subnetWithMask, ipCache, subnetCache) Then
        IsInSubnet = "Yes"
    Else
        IsInSubnet = "No"
    End If
End Function

