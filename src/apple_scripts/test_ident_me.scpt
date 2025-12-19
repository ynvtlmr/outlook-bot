tell application "Microsoft Outlook"
    try
        set inboxFolder to folder "Inbox" of default account
        set msg to item 1 of (get messages of inboxFolder)
        set newDraft to reply to msg
        
        set output to "Draft Created.\n"
        
        try
            set draftSender to sender of newDraft
            set senderAddr to address of draftSender
            set output to output & "Sender Address: " & senderAddr & "\n"
        on error
            set output to output & "Could not get sender directly.\n"
        end try
        
        try
            set draftAccount to account of newDraft
            set acctAddr to email address of draftAccount
            set output to output & "Account Address: " & acctAddr & "\n"
        on error
            set output to output & "Could not get account address.\n"
        end try
        
        close window 1 saving no
        return output
    on error errMsg
        return "Error: " & errMsg
    end try
end tell
