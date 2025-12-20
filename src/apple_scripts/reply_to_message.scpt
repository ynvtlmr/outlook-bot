on run argv
	set msgID to item 1 of argv
	set responseBody to ""
	if (count of argv) > 1 then
		set responseBody to item 2 of argv
	end if
	
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
			
			-- 2.1 Set Content (Prepend) - Done IMMEDIATELY to match successful experiment flow
			try
			    if responseBody is not "" then
			        set oldContent to content of newDraft
			        -- Convert newlines to BR?
			        -- Simple replacement:
			        set newContent to responseBody & "<br>" & oldContent
			        set content of newDraft to newContent
			    end if
			on error e
			    return "Error setting content: " & e
			end try
			
			-- Get my address/name to exclude from recipients
			set myAddress to ""
			set myName to ""
			try
			    set draftSender to sender of newDraft
			    set myAddress to address of draftSender
			    set myName to name of draftSender
			on error
			    -- If direct access fails, try account
			    try
			        set draftAccount to account of newDraft
			        set myAddress to email address of draftAccount
			        set myName to name of draftAccount
			    on error
			    end try
			end try
			
			-- 2.5 CLEANUP: Remove "Me" from the implicitly created recipients
			-- (This happens if we reply to a message we sent ourselves)
			try
			    set existingTo to to recipients of newDraft
			    repeat with r in existingTo
			        try
			             if (address of (get email address of r) is equal to myAddress) or (name of r is equal to myName) then
			                delete r
			             end if
			        on error
			        end try
			    end repeat
			    
			    -- Same for CC? Usually 'reply' doesn't add CC, but good safety
			    set existingCC to cc recipients of newDraft
			    repeat with r in existingCC
			         try
			             if (address of (get email address of r) is equal to myAddress) or (name of r is equal to myName) then
			                delete r
			             end if
			        on error
			        end try
			    end repeat
			on error
			end try
			
			
			-- 3. Simulate Reply All: Copy recipients from TARGET message
			set origTo to to recipients of targetMsg
			set origCC to cc recipients of targetMsg
			
			repeat with r in origTo
			    try
			        set rawAddr to address of (get email address of r)
			        set rawName to "Unknown"
			        try 
			            set rawName to name of r
			        end try
			        
			        if rawAddr is not equal to myAddress and rawName is not equal to myName then
			            -- Check if already exists in draft? (Avoid duplicates if Native Reply added them correctly)
			            -- Simplest: Try adding. Outlook allows dups. 
			            -- Let's check existence to be clean.
			            set alreadyExists to false
			            repeat with ex in (to recipients of newDraft)
			                if (address of (get email address of ex) is equal to rawAddr) then
			                    set alreadyExists to true
			                end if
			            end repeat
			            
			            if not alreadyExists then
			                make new to recipient at newDraft with properties {email address:{address:rawAddr}}
			            end if
			        end if
			    on error e
			        -- log error?
			    end try
			end repeat
			
			repeat with r in origCC
			     try
			         set rawAddr to address of (get email address of r)
			         set rawName to "Unknown"
			         try 
			            set rawName to name of r
			         end try
			         
			         if rawAddr is not equal to myAddress and rawName is not equal to myName then
			             set alreadyExists to false
			             repeat with ex in (cc recipients of newDraft)
			                 if (address of (get email address of ex) is equal to rawAddr) then
			                     set alreadyExists to true
			                 end if
			             end repeat
			             
			             if not alreadyExists then
			                 make new cc recipient at newDraft with properties {email address:{address:rawAddr}}
			             end if
			         end if
			     on error
			     end try
			end repeat
			
			-- 5. Open it
			open newDraft
			
			return "Success: Draft created."
			
		on error errMsg
			return "Error: " & errMsg
		end try
	end tell
end run
