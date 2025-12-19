tell application "Microsoft Outlook"
    try
        set acct to default account
        set props to properties of acct
        return props
    on error
        return "Error getting props"
    end try
end tell
