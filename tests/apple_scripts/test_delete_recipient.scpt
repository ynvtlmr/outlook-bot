tell application "Microsoft Outlook"
    try
        set newDraft to make new outgoing message with properties {subject:"Test Delete"}
        make new to recipient at newDraft with properties {email address:{address:"test@example.com"}}
        
        -- Verify count
        if (count of to recipients of newDraft) is not 1 then return "Setup failed"
        
        -- Try delete
        delete (every to recipient of newDraft)
        
        if (count of to recipients of newDraft) is 0 then
            return "Success: Deleted all."
        else
            return "Failed to delete"
        end if
        
        close window 1 saving no
    on error e
        return "Error: " & e
    end try
end tell
