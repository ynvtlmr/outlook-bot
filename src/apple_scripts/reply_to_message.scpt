on run argv
	set msgID to item 1 of argv
	set responseBody to item 2 of argv
	
	tell application "Microsoft Outlook"
		try
			-- 1. Find the message by ID
			set targetMsg to missing value
			set targetID to msgID as integer
			
			-- Only searching in common folders for speed, or try Getting message by id directly if supported (often not direct)
            -- Actually, 'message id X' often works globally or relative to default account. Let's try globally first.
            -- If fails, we iterate folders.
			try
			    set targetMsg to message id targetID
			on error
			    -- Fallback: Search common folders
			    set searchFolders to {"Inbox", "Sent Items", "Archive", "Deleted Items"}
			    repeat with fName in searchFolders
			        try
			            set f to folder fName of default account
			            set targetMsg to (first message of f where id is targetID)
			            exit repeat
			        on error
			            -- continue
			        end try
			    end repeat
			end try
			
			if targetMsg is missing value then
			    -- Last ditch: check ALL folders
			    set allFolders to every mail folder
			    repeat with f in allFolders
			        try
			             set targetMsg to (first message of f where id is targetID)
			             exit repeat
			        on error
			        end try
			    end repeat
			end if
			
			if targetMsg is missing value then
				return "Error: Message not found with ID " & msgID
			end if
			
			-- 2. Create Reply (This handles the 'From' account automatically)
			set newDraft to reply to targetMsg
			
			-- 3. Simulate Reply All: Copy recipients
			-- Get original recipients
			set origTo to to recipients of targetMsg
			set origCC to cc recipients of targetMsg
			set origSender to sender of targetMsg
			
			-- Add original sender to 'To' (if not already there - Outlook 'reply' does this usually, but let's ensure)
			-- Actually 'reply' puts the sender in 'To'. We just need to add the others.
			
			repeat with r in origTo
			    set rawAddr to address of (get email address of r)
			    make new to recipient at newDraft with properties {email address:{address:rawAddr}}
			end repeat
			
			repeat with r in origCC
			     set rawAddr to address of (get email address of r)
			     make new cc recipient at newDraft with properties {email address:{address:rawAddr}}
			end repeat
			
			-- 4. Set Content (Prepend)
			set currentContent to content of newDraft
			set content of newDraft to responseBody & "\n\n" & currentContent
			
			-- 5. Open it
			open newDraft
			
			return "Success: Draft created."
			
		on error errMsg
			return "Error: " & errMsg
		end try
	end tell
end run
