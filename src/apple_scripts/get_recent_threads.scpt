tell application "Microsoft Outlook"
	set msgList to {}
	set scanLimit to 50
	
	try
		set totalCount to count of messages of inbox
	on error
		return "Error: Could not access Inbox"
	end try
	
	if totalCount = 0 then
		return ""
	end if
	
	if totalCount < scanLimit then
		set startIndex to 1
	else
		set startIndex to totalCount - scanLimit + 1
	end if
	
	repeat with i from totalCount to startIndex by -1
		try
			set msg to message i of inbox
			
			set msgSender to sender of msg
			set senderAddress to address of msgSender
			set senderName to name of msgSender
			set msgSubject to subject of msg
			set msgContent to plain text content of msg
			set msgDate to time sent of msg
			
			try
				set msgConvID to conversation id of msg
			on error
				set msgConvID to "NO_ID"
			end try
			
			set entry to "ID: " & msgConvID & "\n" & "From: " & senderName & " <" & senderAddress & ">\n" & "Date: " & msgDate & "\n" & "Subject: " & msgSubject & "\n" & "---BODY_START---\n" & msgContent & "\n---BODY_END---"
			
			set end of msgList to entry
		on error errMsg
			-- Ignore single message errors
		end try
	end repeat
	
	set AppleScript's text item delimiters to "\n///END_OF_MESSAGE///\n"
	return msgList as text
end tell
