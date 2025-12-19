tell application "Microsoft Outlook"
	set msgList to {}
	set visitedIDs to {}
	
	-- 1. Find all flagged messages (Active or Completed)
	-- We look in all folders or just key ones? Scanning all folders is slow.
	-- Let's stick to the previous logic of scanning all folders to FIND the flags.
	
	set allFolders to every mail folder
	set flaggedConversationIDs to {}
	
	repeat with currentFolder in allFolders
		try
			set foundMessages to (every message of currentFolder where todo flag is not not flagged)
			repeat with msg in foundMessages
				try
					set cID to conversation id of msg
					if cID is not in flaggedConversationIDs then
						set end of flaggedConversationIDs to cID
					end if
				on error
					-- skip if no conversation id
				end try
			end repeat
		on error
			-- skip folder error
		end try
	end repeat
	
	-- 2. For each conversation ID, fetch ALL messages from key folders
	-- Scanning EVERY folder for EVERY conversation is O(N*M) and too slow.
	-- We will look in "Inbox", "Sent Items", "Archive", and "Deleted Items"
	set searchFolderNames to {"Inbox", "Sent Items", "Archive", "Deleted Items"}
	set searchFolders to {}
	
	repeat with fName in searchFolderNames
		try
			set end of searchFolders to (every mail folder where name is fName)
		on error
			-- ignore missing folders
		end try
	end repeat
	-- Flatten list if needed (AppleScript list handling is weird, but 'every mail folder' returns a list)
	
	repeat with cID in flaggedConversationIDs
		set threadMessages to {}
		
		-- Search in our target folders
		-- Note: We have a list of lists of folders potentially, need to be careful
		repeat with folderList in searchFolders
			repeat with f in folderList
				try
					set foundMsgs to (every message of f where conversation id is cID)
					set threadMessages to threadMessages & foundMsgs
				on error
					-- ignore
				end try
			end repeat
		end repeat
		
		-- Also search inside the folder where we found the flag originally? 
		-- actually, the above set covers the main ones.
		
		-- Process messages
		repeat with msg in threadMessages
			try
				set msgSender to sender of msg
				set senderAddress to address of msgSender
				set senderName to name of msgSender
				set msgSubject to subject of msg
				set msgContent to plain text content of msg
				set msgDate to time sent of msg
				set msgID to id of msg -- internal ID to avoid duplicates?
				
				-- Check for duplicates? For now assume folders don't overlap messages much (except copies)
				
				-- Get Flag Status
				set flagStatusRaw to todo flag of msg
				set flagStatus to "None"
				if flagStatusRaw is not completed then
					set flagStatus to "Active"
				else if flagStatusRaw is completed then
					set flagStatus to "Completed"
				end if
				
				set entry to "ID: " & cID & "\n" & "From: " & senderName & " <" & senderAddress & ">\n" & "Date: " & msgDate & "\n" & "Subject: " & msgSubject & "\n" & "FlagStatus: " & flagStatus & "\n" & "---BODY_START---\n" & msgContent & "\n---BODY_END---"
				
				set end of msgList to entry
			on error errMsg
				-- Ignore single message errors
			end try
		end repeat
		
	end repeat
	
	set AppleScript's text item delimiters to "\n///END_OF_MESSAGE///\n"
	return msgList as text
end tell
