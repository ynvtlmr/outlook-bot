tell application "Microsoft Outlook"
	set msgList to {}
	set scanLimit to 50
	
	set allInboxes to every mail folder where name is "Inbox"
	
	repeat with currentInbox in allInboxes
		try
			set totalCount to count of messages of currentInbox
			
			if totalCount > 0 then
				if totalCount < scanLimit then
					set startIndex to 1
				else
					set startIndex to totalCount - scanLimit + 1
				end if
				
				repeat with i from totalCount to startIndex by -1
					try
						set msg to message i of currentInbox
						
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
			end if
		on error
			-- Ignore errors accessing specific inbox
		end try
	end repeat
	
	set AppleScript's text item delimiters to "\n///END_OF_MESSAGE///\n"
	return msgList as text
end tell
