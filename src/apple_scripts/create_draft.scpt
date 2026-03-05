on run argv
    set recipientAddress to item 1 of argv
    set msgSubject to item 2 of argv
    set msgContent to item 3 of argv

    set bccAddress to ""
    if (count of argv) > 3 then
        set bccAddress to item 4 of argv
    end if

    tell application "Microsoft Outlook"
        set newInfo to {subject:msgSubject, content:msgContent}
        set newMsg to make new outgoing message with properties newInfo
        make new recipient at newMsg with properties {email address:{address:recipientAddress}}

        if bccAddress is not "" then
            make new bcc recipient at newMsg with properties {email address:{address:bccAddress}}
        end if

        open newMsg -- Opens the draft for review instead of trying to save silently
    end tell

    return "Draft created"
end run
