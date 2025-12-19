tell application "Microsoft Outlook"
    set output to ""
    set inboxFolder to folder "Inbox" of default account
    set msg to item 1 of (get messages of inboxFolder)
    
    -- Variant 1: reply to with reply to all
    try
        set r to reply to msg with reply to all
        set output to output & "Variant 1 Success\n"
        close window 1 saving no
    on error
        set output to output & "Variant 1 Failed\n"
    end try
    
    -- Variant 2: reply all
    try
        reply all to msg
        set output to output & "Variant 2 Success\n"
        close window 1 saving no
    on error
        set output to output & "Variant 2 Failed\n"
    end try
    
    return output
end tell
