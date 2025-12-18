on run argv
    set recipientAddress to item 1 of argv
    set msgSubject to item 2 of argv
    set msgContent to item 3 of argv
    
    tell application "Microsoft Outlook"
        set newInfo to {subject:msgSubject, content:msgContent}
        set newMsg to make new outgoing message with properties newInfo
        make new recipient at newMsg with properties {email address:{address:recipientAddress}}
        save newMsg -- Saves to Drafts
    end tell
    
    return "Draft created"
end run
