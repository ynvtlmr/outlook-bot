tell application "Microsoft Outlook"
    try
        -- Get the first message of Inbox
        set inboxFolder to folder "Inbox" of default account
        set msg to item 1 of (get messages of inboxFolder)
        
        -- Try reply all
        set replyMsg to reply all to msg
        
        set output to "Success: Created reply ALL object.\n"
        set output to output & "Subject: " & subject of replyMsg & "\n"
        
        -- Clean up
        close window 1 saving no
        
        return output
    on error errMsg
        return "Error: " & errMsg
    end try
end tell
