tell application "Microsoft Outlook"
    set output to ""
    try
        set targetFolder to item 1 of (every mail folder where name is "Inbox" and unread count > 0)
        set output to output & "Checking folder: " & name of targetFolder & "\n"
        
        set msgs to messages 1 thru 10 of targetFolder
        repeat with msg in msgs
            try
                set s to subject of msg
                set f to todo flag of msg
                set output to output & "Subject: " & s & " | Flag: " & f & "\n"
            on error errMsg
                set output to output & "Error reading msg: " & errMsg & "\n"
            end try
        end repeat
    on error errMsg
        set output to output & "Global Error: " & errMsg
    end try
    return output
end tell
