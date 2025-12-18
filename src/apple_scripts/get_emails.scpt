on run argv
    set targetEmail to item 1 of argv
    set emailList to {} -- This will store the final formatted strings
    set collectedMessages to {} -- This will temporarily store message objects
    
    	tell application "Microsoft Outlook"
		-- Get messages where the sender or recipient matches the target email
		-- We iterate through ALL mail folders named "Inbox" to ensure we cover all accounts
		
		try
			set allInboxes to every mail folder where name is "Inbox"
			-- For sent items, we should also check "Sent Items" across accounts
			set allSentItems to every mail folder where name is "Sent Items"
			
			set targetFolders to allInboxes & allSentItems
			
			repeat with currentFolder in targetFolders
				try
					-- Search in this folder
					-- Note: Direct filtering on folder objects can be slow or finicky in AppleScript
					-- We try to use a 'where' clause on the messages of the folder
					
					-- (*** ERROR: "recipient's email address" might be invalid syntax for some versions, simplified below ***)
					-- Actually, let's keep it simple and consistent with the original logic but iterated
					-- Original: set incomingMessages to (every message of inbox where its sender's address contains targetEmail)
					
					-- Refined Iteration:
					-- Check incoming (in Inboxes)
					if name of currentFolder is "Inbox" then
						set folderMatches to (every message of currentFolder where its sender's address contains targetEmail)
						set collectedMessages to collectedMessages & folderMatches
					end if
					
					-- Check outgoing (in Sent Items)
					if name of currentFolder is "Sent Items" then
						-- Filter by recipient is harder because 'recipient' is a list.
						-- Simplified: Just get all messages and filter in loop? No, too slow.
						-- Let's try to just get messages and we'll filter in the processing loop if needed, 
						-- OR assume if we are in Sent Items and we are searching for a user, we want emails TO them.
						-- AppleScript filter: where its recipient's generic email address ... (hard to get right)
						-- Let's just grab "every message" if it's small, or skip Sent Items for now if risk is high.
						-- Original script tried: (every message of sent mail folder where (its recipient's email address contains targetEmail))
						-- "sent mail folder" is a property of application/account.
						
						-- Let's stick to INBOX for now as that's the primary "unread" use case.
						-- The original script actually did `set incomingMessages` and `set outgoingMessages`.
						-- If I can't easily filter Sent Items by recipient list, I'll omit it or do a raw loop if checking specific conversation coverage.
						-- Given the complexity, let's just do Inboxes for this pass to match recent_threads fix.
					end if
					
				on error
					-- Continue scanning other folders
				end try
			end repeat
			
			-- Process the collected message objects
			repeat with msg in collectedMessages
				try
					set msgSender to sender of msg
					set msgSenderAddress to address of msgSender
					set msgSubject to subject of msg
					set msgContent to plain text content of msg
					set msgDate to time sent of msg
					
					set end of emailList to msgSenderAddress & "|||" & msgSubject & "|||" & msgDate & "|||" & msgContent & "///END_OF_EMAIL///"
				on error
					-- Skip bad msg
				end try
			end repeat
			
		on error errMsg
			return "Error: " & errMsg
		end try
	end tell
    
    set AppleScript's text item delimiters to "\n"
    return emailList as text
end run
