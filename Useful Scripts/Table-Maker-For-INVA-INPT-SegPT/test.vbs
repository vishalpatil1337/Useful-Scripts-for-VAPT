Option Explicit

' Create basic objects
Dim objFSO, objExcel, objWB
Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objExcel = CreateObject("Excel.Application")
objExcel.Visible = True
Set objWB = objExcel.Workbooks.Add

' Check if file exists
If Not objFSO.FileExists("scope.txt") Then
    WScript.Echo "scope.txt not found."
    WScript.Quit
End If

' Read file and collect sections and IPs
Dim objFile, strLine, strCurrentSection
Dim dictSections, dictSectionIPs
Set dictSections = CreateObject("Scripting.Dictionary")
Set dictSectionIPs = CreateObject("Scripting.Dictionary")

' First pass - read sections
Set objFile = objFSO.OpenTextFile("scope.txt", 1)
strCurrentSection = "Main"

' Add default section
dictSections.Add strCurrentSection, ""

Do Until objFile.AtEndOfStream
    strLine = Trim(objFile.ReadLine)
    If strLine <> "" Then
        If InStr(strLine, ":") > 0 Then
            ' This is a section header
            strCurrentSection = strLine
            If Not dictSections.Exists(strCurrentSection) Then
                dictSections.Add strCurrentSection, ""
            End If
        End If
    End If
Loop
objFile.Close

' Initialize section IP arrays
Dim secName
For Each secName In dictSections.Keys
    dictSectionIPs.Add secName, CreateObject("Scripting.Dictionary")
Next

' Second pass - collect IPs for each section
Set objFile = objFSO.OpenTextFile("scope.txt", 1)
strCurrentSection = "Main"

Do Until objFile.AtEndOfStream
    strLine = Trim(objFile.ReadLine)
    If strLine <> "" Then
        If InStr(strLine, ":") > 0 Then
            ' Change current section
            strCurrentSection = strLine
        Else
            ' Add IP to current section
            Dim ipCount
            ipCount = dictSectionIPs(strCurrentSection).Count
            dictSectionIPs(strCurrentSection).Add ipCount, strLine
        End If
    End If
Loop
objFile.Close

' Set zoom level for better visibility
objExcel.ActiveWindow.Zoom = 100

' Create a sheet for each section with IPs
Dim objSheet, sheetName, i, j, k
Dim row1, row2, row3, row4

For Each secName In dictSections.Keys
    ' Skip empty sections
    If dictSectionIPs(secName).Count > 0 Then
        ' Create safe sheet name
        sheetName = Replace(secName, ":", "")
        sheetName = Replace(sheetName, " ", "_")
        If Len(sheetName) > 31 Then
            sheetName = Left(sheetName, 31)
        End If
        
        ' Create sheet
        Set objSheet = objWB.Sheets.Add
        objSheet.Name = sheetName
        
        ' Add section name as title
        objSheet.Range("A1:F1").Merge
        objSheet.Cells(1, 1).Value = "Subnet Inventory: " & secName
        objSheet.Cells(1, 1).Font.Size = 14
        objSheet.Cells(1, 1).Font.Bold = True
        objSheet.Cells(1, 1).HorizontalAlignment = -4108 ' Center alignment
        
        ' Add headers
        objSheet.Cells(3, 1).Value = "Column A"
        objSheet.Cells(3, 2).Value = "Column B"
        objSheet.Cells(3, 3).Value = "Column C"
        objSheet.Cells(3, 4).Value = "Column D"
        objSheet.Range("A3:D3").Font.Bold = True
        objSheet.Range("A3:D3").Interior.Color = RGB(242, 242, 242)
        objSheet.Range("A3:D3").Borders.LineStyle = 1
        objSheet.Range("A3:D3").HorizontalAlignment = -4108 ' Center alignment
        
        ' Get IPs for this section
        Dim sectionIPs, ipKey, ipValue, ipIndex, totalIPs
        Set sectionIPs = dictSectionIPs(secName)
        totalIPs = sectionIPs.Count
        
        ' Improved distribution logic:
        ' Calculate base IPs per table (rounded down)
        Dim baseIPsPerTable, extraIPs
        baseIPsPerTable = totalIPs \ 4  ' Integer division
        extraIPs = totalIPs Mod 4
        
        ' Distribute IPs for each column
        Dim currentIndex, rowsForColumn, currentRow, currentCol
        
        currentIndex = 0
        
        ' First determine how many rows for each column
        Dim rowsCol1, rowsCol2, rowsCol3, rowsCol4
        
        ' Base distribution
        rowsCol1 = baseIPsPerTable
        rowsCol2 = baseIPsPerTable
        rowsCol3 = baseIPsPerTable
        rowsCol4 = baseIPsPerTable
        
        ' Distribute extra IPs across columns starting from the left (per your requirements)
        If extraIPs > 0 Then rowsCol1 = rowsCol1 + 1
        If extraIPs > 1 Then rowsCol2 = rowsCol2 + 1
        If extraIPs > 2 Then rowsCol3 = rowsCol3 + 1
        
        ' Fill column 1 with IPs (NO bullet points)
        For i = 0 To rowsCol1 - 1
            If currentIndex < totalIPs Then
                objSheet.Cells(i + 4, 1).Value = sectionIPs(currentIndex)
                currentIndex = currentIndex + 1
            End If
        Next
        
        ' Fill column 2 with IPs (NO bullet points)
        For i = 0 To rowsCol2 - 1
            If currentIndex < totalIPs Then
                objSheet.Cells(i + 4, 2).Value = sectionIPs(currentIndex)
                currentIndex = currentIndex + 1
            End If
        Next
        
        ' Fill column 3 with IPs (NO bullet points)
        For i = 0 To rowsCol3 - 1
            If currentIndex < totalIPs Then
                objSheet.Cells(i + 4, 3).Value = sectionIPs(currentIndex)
                currentIndex = currentIndex + 1
            End If
        Next
        
        ' Fill column 4 with IPs (NO bullet points)
        For i = 0 To rowsCol4 - 1
            If currentIndex < totalIPs Then
                objSheet.Cells(i + 4, 4).Value = sectionIPs(currentIndex)
                currentIndex = currentIndex + 1
            End If
        Next
        
        ' Calculate row count for statistics (max rows used + 5 for spacing)
        Dim maxRows
        maxRows = rowsCol1
        If rowsCol2 > maxRows Then maxRows = rowsCol2
        If rowsCol3 > maxRows Then maxRows = rowsCol3
        If rowsCol4 > maxRows Then maxRows = rowsCol4
        
        ' Add statistics section in column G
        ' Title for statistics section
        objSheet.Range("G3:J3").Merge
        objSheet.Cells(3, 7).Value = "IP Statistics Summary"
        objSheet.Cells(3, 7).Font.Bold = True
        objSheet.Cells(3, 7).Interior.Color = RGB(0, 112, 192)
        objSheet.Cells(3, 7).Font.Color = RGB(255, 255, 255)
        objSheet.Cells(3, 7).HorizontalAlignment = -4108 ' Center alignment
        
        ' Add statistics table headers
        objSheet.Cells(4, 7).Value = "Metric"
        objSheet.Cells(4, 8).Value = "Value"
        objSheet.Range("G4:J4").Font.Bold = True
        objSheet.Range("G4:J4").Interior.Color = RGB(242, 242, 242)
        objSheet.Range("G4:J4").Borders.LineStyle = 1
        
        ' Column counts
        objSheet.Cells(5, 7).Value = "Column A Count:"
        objSheet.Cells(5, 8).Value = rowsCol1 & " subnets"
        
        objSheet.Cells(6, 7).Value = "Column B Count:"
        objSheet.Cells(6, 8).Value = rowsCol2 & " subnets"
        
        objSheet.Cells(7, 7).Value = "Column C Count:"
        objSheet.Cells(7, 8).Value = rowsCol3 & " subnets"
        
        objSheet.Cells(8, 7).Value = "Column D Count:"
        objSheet.Cells(8, 8).Value = rowsCol4 & " subnets"
        
        ' Total subnets
        objSheet.Cells(9, 7).Value = "Total Subnets:"
        objSheet.Cells(9, 8).Value = totalIPs
        objSheet.Cells(9, 7).Font.Bold = True
        objSheet.Cells(9, 8).Font.Bold = True
        
        ' Calculate total IP addresses in scope
        Dim totalAddresses, ipAddressCountMatch, ipAddressMask, ipAddressCount
        totalAddresses = 0
        
        For ipIndex = 0 To totalIPs - 1
            ' Extract CIDR mask from IP (e.g., /24, /23, etc.)
            If InStr(sectionIPs(ipIndex), "/") > 0 Then
                ipAddressCountMatch = Trim(Mid(sectionIPs(ipIndex), InStr(sectionIPs(ipIndex), "/") + 1))
                
                If IsNumeric(ipAddressCountMatch) Then
                    ipAddressMask = CInt(ipAddressCountMatch)
                    ' Calculate addresses from CIDR notation (2^(32-mask))
                    ipAddressCount = 2 ^ (32 - ipAddressMask)
                    totalAddresses = totalAddresses + ipAddressCount
                End If
            End If
        Next
        
        ' Total IP Addresses
        objSheet.Cells(10, 7).Value = "Total IP Addresses:"
        objSheet.Cells(10, 8).Value = totalAddresses
        objSheet.Cells(10, 7).Font.Bold = True
        objSheet.Cells(10, 8).Font.Bold = True
        
        ' Add section name 
        objSheet.Cells(11, 7).Value = "Section Name:"
        objSheet.Cells(11, 8).Value = secName
        
        ' Format the statistics section
        objSheet.Range("G3:J11").Borders.LineStyle = 1
        objSheet.Range("G3:H11").BorderAround 1, 2
        
        ' Auto-fit columns for content
        objSheet.Columns("A:J").AutoFit
        
        ' Set minimum width for data columns
        For i = 1 To 4
            If objSheet.Columns(i).ColumnWidth < 20 Then
                objSheet.Columns(i).ColumnWidth = 20
            End If
        Next
        
        ' Set minimum width for statistics columns
        If objSheet.Columns(7).ColumnWidth < 18 Then
            objSheet.Columns(7).ColumnWidth = 18
        End If
        If objSheet.Columns(8).ColumnWidth < 18 Then
            objSheet.Columns(8).ColumnWidth = 18
        End If
        
        ' Add alternating row colors for better readability
        For i = 4 To maxRows + 3
            If i Mod 2 = 0 Then
                objSheet.Range(objSheet.Cells(i, 1), objSheet.Cells(i, 4)).Interior.Color = RGB(240, 240, 240)
            End If
        Next
        
        ' Add borders to the data grid
        objSheet.Range(objSheet.Cells(3, 1), objSheet.Cells(maxRows + 3, 4)).Borders.LineStyle = 1
        objSheet.Range(objSheet.Cells(3, 1), objSheet.Cells(maxRows + 3, 4)).BorderAround 1, 2
        
        ' Create a new worksheet for formatted copy-paste with bullet points
        Dim copySheet
        Set copySheet = objWB.Sheets.Add
        copySheet.Name = sheetName & "_CopyPaste"
        
        ' Add a header to the copy-paste sheet
        copySheet.Range("A1:D1").Merge
        copySheet.Cells(1, 1).Value = "Formatted IPs for Copy-Paste (with Bullet Points)"
        copySheet.Cells(1, 1).Font.Bold = True
        copySheet.Cells(1, 1).HorizontalAlignment = -4108 ' Center
        
        ' Create Word-friendly bullet points using character code 8226 (•)
        Dim bulletChar
        bulletChar = ChrW(8226)
        
        ' Reset counters and copy IPs with proper bullet formatting
        currentIndex = 0
        
        ' Fill column 1 with bullet IPs
        For i = 0 To rowsCol1 - 1
            If currentIndex < totalIPs Then
                copySheet.Cells(i + 3, 1).Value = bulletChar & " " & sectionIPs(currentIndex)
                currentIndex = currentIndex + 1
            End If
        Next
        
        ' Fill column 2 with bullet IPs
        For i = 0 To rowsCol2 - 1
            If currentIndex < totalIPs Then
                copySheet.Cells(i + 3, 2).Value = bulletChar & " " & sectionIPs(currentIndex)
                currentIndex = currentIndex + 1
            End If
        Next
        
        ' Fill column 3 with bullet IPs
        For i = 0 To rowsCol3 - 1
            If currentIndex < totalIPs Then
                copySheet.Cells(i + 3, 3).Value = bulletChar & " " & sectionIPs(currentIndex)
                currentIndex = currentIndex + 1
            End If
        Next
        
        ' Fill column 4 with bullet IPs
        For i = 0 To rowsCol4 - 1
            If currentIndex < totalIPs Then
                copySheet.Cells(i + 3, 4).Value = bulletChar & " " & sectionIPs(currentIndex)
                currentIndex = currentIndex + 1
            End If
        Next
        
        ' Format the copySheet
        copySheet.Columns("A:D").AutoFit
        For i = 1 To 4
            If copySheet.Columns(i).ColumnWidth < 20 Then
                copySheet.Columns(i).ColumnWidth = 20
            End If
        Next
        
        ' Add instructional note
        copySheet.Range("A2:D2").Merge
        copySheet.Cells(2, 1).Value = "Select and copy the cells below to paste into Word with bullet formatting intact"
        copySheet.Cells(2, 1).Font.Italic = True
        copySheet.Cells(2, 1).HorizontalAlignment = -4108 ' Center
    End If
Next

' Delete the default sheet if we created others
If objWB.Sheets.Count > 1 Then
    objWB.Sheets(1).Delete
End If

' Save workbook
objWB.SaveAs objFSO.GetAbsolutePathName("IP_Inventory.xlsx")
WScript.Echo "Excel file created with professional formatting and statistics."