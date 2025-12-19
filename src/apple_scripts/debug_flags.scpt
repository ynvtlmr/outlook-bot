tell application "Microsoft Outlook"
    set output to "Scanning folders for flags...\n"
    set totalFlagged to 0
    
    try
        set allFolders to every mail folder
        repeat with f in allFolders
            try
                set fName to name of f
                -- optimized counting
                set markedCount to count of (messages of f where todo flag is marked)
                
                if markedCount > 0 then
                    set output to output & "Folder: " & fName & " - Marked: " & markedCount & "\n"
                    set totalFlagged to totalFlagged + markedCount
                end if
            on error errMsg
                 -- set output to output & "Error in " & name of f & ": " & errMsg & "\n"
            end try
        end repeat
    on error errMsg
        set output to output & "Global Error: " & errMsg
    end try
    
    set output to output & "Total Flagged Found: " & totalFlagged
    return output
end tell
