on run argv
    set recipientAddress to item 1 of argv
    set msgSubject to item 2 of argv
    set msgContent to item 3 of argv
    
    set bccAddress to ""
    if (count of argv) > 3 then
        set bccAddress to item 4 of argv
    end if
    
    tell application "Microsoft Outlook"
        set newInfo to {subject:msgSubject}
        set newMsg to make new outgoing message with properties newInfo
        make new recipient at newMsg with properties {email address:{address:recipientAddress}}
        
        -- Add BCC if provided
        if bccAddress is not "" then
            try
                make new bcc recipient at newMsg with properties {email address:{address:bccAddress}}
            on error
                -- Log error if needed
            end try
        end if
        
        open newMsg -- Opens the draft for review
        delay 1.0 -- Wait for window to open
    end tell
    
    -- Set content using UI automation (similar to reply_to_message.scpt)
    try
        if msgContent is not "" then
            -- Convert HTML <br> to newlines for typing
            set AppleScript's text item delimiters to "<br>"
            set textItems to text items of msgContent
            set AppleScript's text item delimiters to return
            set plainTextBody to textItems as string
            set AppleScript's text item delimiters to ""
            
            -- Use System Events to type the text directly into the draft window
            tell application "System Events"
                tell process "Microsoft Outlook"
                    -- Activate Outlook first
                    set frontmost to true
                    delay 0.5
                    
                    -- Wait for window to be ready
                    set maxRetries to 10
                    set retryCount to 0
                    set windowReady to false
                    
                    repeat while not windowReady and retryCount < maxRetries
                        try
                            set winCount to count of windows
                            if winCount > 0 then
                                try
                                    set bodyField to first text area of window 1
                                    set windowReady to true
                                on error
                                    set retryCount to retryCount + 1
                                    delay 0.5
                                end try
                            else
                                set retryCount to retryCount + 1
                                delay 0.5
                            end if
                        on error
                            set retryCount to retryCount + 1
                            delay 0.5
                        end try
                    end repeat
                    
                    delay 1.0
                    
                    -- Type the content
                    set typingSuccess to false
                    set attemptCount to 0
                    set maxAttempts to 3
                    
                    repeat while not typingSuccess and attemptCount < maxAttempts
                        try
                            set attemptCount to attemptCount + 1
                            set bodyField to first text area of window 1
                            click bodyField
                            delay 0.3
                            click bodyField
                            delay 0.3
                            key code 126 using command down -- Command+Up Arrow
                            delay 0.2
                            keystroke plainTextBody
                            delay 0.5
                            set typingSuccess to true
                        on error
                            if attemptCount < maxAttempts then
                                delay 1.0
                            end if
                        end try
                    end repeat
                end tell
            end tell
        end if
    on error errMsg
        -- If UI automation fails, try setting content property directly
        try
            tell application "Microsoft Outlook"
                set content of newMsg to plainTextBody
            end tell
        on error
            -- If that also fails, return error
            return "Error setting content: " & errMsg
        end try
    end try
    
    return "Draft created"
end run
