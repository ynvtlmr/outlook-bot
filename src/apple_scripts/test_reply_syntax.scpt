tell application "Microsoft Outlook"
    try
        -- Get the most recent message in Inbox to test syntax (won't actually save unless we tell it to)
        set msg to item 1 of (get messages of folder "Inbox" of default account)
        
        -- Try to create a reply
        set replyMsg to reply to msg without opening window
        
        set output to "Success: Created reply object.\n"
        set output to output & "Subject: " & subject of replyMsg & "\n"
        
        -- Check if we can get the account
        set acct to account of replyMsg
        set output to output & "Account: " & name of acct
        
        discard replyMsg -- Don't keep junk
        return output
    on error errMsg
        return "Error: " & errMsg
    end try
end tell
