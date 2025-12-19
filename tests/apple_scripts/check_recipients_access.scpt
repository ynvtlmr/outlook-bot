tell application "Microsoft Outlook"
    set output to ""
    try
        set inboxFolder to folder "Inbox" of default account
        set msg to item 1 of (get messages of inboxFolder)
        
        -- Attempt 1: 'reply to' with 'all' parameter (rare but possible)
        try
           -- Some versions use 'reply to all' as a boolean param? No standard docs support this but worth a shot
           -- set r to reply to msg with reply all
           -- This usually fails compilation.
        end try

        -- Attempt 2: Creating a draft and setting recipients?
        -- This is the "Simulation" method, confirming we can read recipients
        set ccList to cc recipients of msg
        set toList to to recipients of msg
        
        set output to output & "Can read recipients? Yes. Count: " & (count of toList) & "\n"
        
        return output
    on error errMsg
        return "Error: " & errMsg
    end try
end tell
