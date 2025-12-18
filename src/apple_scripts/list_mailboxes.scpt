tell application "Microsoft Outlook"
    set output to "Listing Top Mail Folders...\n"
    try
        set topMailFolders to every mail folder
        repeat with f in topMailFolders
            set fName to name of f
            set unreadCount to unread count of f
            set output to output & " - " & fName & " (Unread: " & unreadCount & ")"
            try
                set containerName to name of container of f
                set output to output & " [Container: " & containerName & "]"
            on error
                set output to output & " [No Container/Root]"
            end try
            set output to output & "\n"
        end repeat
    on error errMsg
        set output to output & "Error: " & errMsg & "\n"
    end try

    return output
end tell
