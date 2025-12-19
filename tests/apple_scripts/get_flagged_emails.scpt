tell application "Microsoft Outlook"
	set msgList to {}
	
	-- Get all top-level mail folders
	set allFolders to every mail folder
	
	repeat with currentFolder in allFolders
		try
		    -- Find flagged messages in this folder
		    -- Note: 'todo flag' is the property. 'status' can be 'flagged' or 'completed'.
			-- Changed from 'is marked' to 'is not not flagged' to catch all states, then we can filter if needed.
			-- However, purely 'not not flagged' is safest for discovery. 
			set flaggedMessages to (every message of currentFolder where todo flag is not not flagged)
			
			repeat with msg in flaggedMessages
				try
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
		on error
			-- Ignore errors accessing specific folder
		end try
	end repeat
	
	set AppleScript's text item delimiters to "\n///END_OF_MESSAGE///\n"
	return msgList as text
end tell
