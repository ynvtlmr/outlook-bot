on run argv
    set targetEmail to item 1 of argv
    set emailList to {}
    
    tell application "Microsoft Outlook"
        -- Get messages where the sender or recipient matches the target email
        -- Note: This is a simplified query. Outlook AppleScript support can be tricky with complex filters.
        -- We will fetch recent messages and filter in Python if needed, but let's try to filter here for efficiency.
        
        try
            set incomingMessages to (every message of inbox where its sender's address contains targetEmail)
            set outgoingMessages to (every message of sent mail folder where (its recipient's email address contains targetEmail)) -- simplified, might need iteration
            
            -- Combine lists (simplified for this script, better to do one folder at a time or use a search)
            -- For robustness, let's just search the inbox for now as per "read all the emails... user has on their outlook client".
            -- Searching all folders is slow. Let's stick to Inbox and Sent Items for the MVP.
            
            set allMessages to incomingMessages & outgoingMessages
            
            repeat with msg in allMessages
                set msgSender to sender of msg
                set msgSenderAddress to address of msgSender
                set msgSubject to subject of msg
                set msgContent to plain text content of msg
                set msgDate to time sent of msg
                
                -- Format: SENDER|SUBJECT|DATE|CONTENT_PREVIEW (or full content)
                -- We use a delimiter that is unlikely to be in the text, e.g. "|||"
                set end of emailList to msgSenderAddress & "|||" & msgSubject & "|||" & msgDate & "|||" & msgContent & "///END_OF_EMAIL///"
            end repeat
            
        on error errMsg
            return "Error: " & errMsg
        end try
    end tell
    
    set AppleScript's text item delimiters to "\n"
    return emailList as text
end run
