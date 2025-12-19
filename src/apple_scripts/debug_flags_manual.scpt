tell application "Microsoft Outlook"
    set output to "Manual Flag Scan...\n"
    
    try
        -- targeted scan on the known active inbox
        set targetFolders to (every mail folder where name is "Inbox")
        
        repeat with f in targetFolders
            try
                set msgCount to count of messages of f
                if msgCount > 0 then
                    set output to output & "Scanning " & name of f & " (" & msgCount & " msgs)...\n"
                    -- Check first 100
                    set checkLimit to 100
                    if msgCount < 100 then set checkLimit to msgCount
                    
                    set subdirMsgs to messages 1 thru checkLimit of f
                    repeat with msg in subdirMsgs
                        set tf to todo flag of msg
                        if tf is not not flagged then
                             set output to output & "FOUND FLAG: " & tf & " | Subj: " & subject of msg & "\n"
                        end if
                    end repeat
                end if
            on error errMsg
                -- ignore
            end try
        end repeat
        
    on error errMsg
        set output to output & "Global Error: " & errMsg
    end try
    
    return output
end tell
