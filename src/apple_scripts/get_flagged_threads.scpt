tell application "Microsoft Outlook"
	set msgList to {}
	set visitedMsgIDs to {}

	-- 1. Scan only key folders (not every folder) for flagged conversation IDs
	set searchFolderNames to {"Inbox", "Sent Items", "Archive"}
	set searchFolders to {}

	repeat with fName in searchFolderNames
		try
			set matchedFolders to (every mail folder where name is fName)
			repeat with f in matchedFolders
				set end of searchFolders to f
			end repeat
		on error
			-- ignore missing folders
		end try
	end repeat

	-- Collect flagged conversation IDs from these folders only
	set flaggedConversationIDs to {}

	repeat with f in searchFolders
		try
			set foundMessages to (every message of f where todo flag is not not flagged)
			repeat with msg in foundMessages
				try
					if todo flag of msg is not completed then
						set cID to conversation id of msg
						if cID is not in flaggedConversationIDs then
							set end of flaggedConversationIDs to cID
						end if
					end if
				on error
					-- skip if no conversation id
				end try
			end repeat
		on error
			-- skip folder error
		end try
	end repeat

	-- 2. For each conversation ID, fetch messages from the same folders
	--    Track visited message IDs to skip duplicates across folders
	repeat with cID in flaggedConversationIDs
		repeat with f in searchFolders
			try
				set foundMsgs to (every message of f where conversation id is cID)
				repeat with msg in foundMsgs
					try
						set msgID to id of msg

						-- Skip duplicates
						if msgID is in visitedMsgIDs then
							-- already processed
						else
							set end of visitedMsgIDs to msgID

							set msgSender to sender of msg
							set senderAddress to address of msgSender
							set senderName to name of msgSender
							set msgSubject to subject of msg
							set msgDate to time sent of msg

							-- Truncate body to first 2000 chars to avoid IPC bloat
							set msgContent to plain text content of msg
							if (count of msgContent) > 2000 then
								set msgContent to text 1 thru 2000 of msgContent
							end if

							set flagStatusRaw to todo flag of msg
							set flagStatus to "None"
							if flagStatusRaw is completed then
								set flagStatus to "Completed"
							else if flagStatusRaw is not not flagged then
								set flagStatus to "Active"
							end if

							set entry to "ID: " & cID & "\n" & "MessageID: " & msgID & "\n" & "From: " & senderName & " <" & senderAddress & ">\n" & "Date: " & msgDate & "\n" & "Subject: " & msgSubject & "\n" & "FlagStatus: " & flagStatus & "\n" & "---BODY_START---\n" & msgContent & "\n---BODY_END---"

							set end of msgList to entry
						end if
					on error errMsg
						-- Ignore single message errors
					end try
				end repeat
			on error
				-- ignore folder query error
			end try
		end repeat
	end repeat

	set AppleScript's text item delimiters to "\n///END_OF_MESSAGE///\n"
	return msgList as text
end tell
