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
			
			-- Wait for draft window to fully open and initialize
			-- Increased delay for "cold start" - first draft needs more time
			delay 3.5
			
			-- 2.1 Set Content - Using UI Automation (keystrokes) to bypass content property limitations
			try
			    if responseBody is not "" then
			        -- Convert HTML <br> to newlines for typing
			        set AppleScript's text item delimiters to "<br>"
			        set textItems to text items of responseBody
			        set AppleScript's text item delimiters to return
			        set plainTextBody to textItems as string
			        set AppleScript's text item delimiters to ""
			        
			        -- Use System Events to type the text directly into the draft window
			        tell application "System Events"
			            tell process "Microsoft Outlook"
			                -- Activate the window and ensure it's ready
			                set frontmost to true
			                delay 1.0
			                
			                -- Verify window exists and is ready
			                try
			                    set winCount to count of windows
			                    if winCount is 0 then
			                        -- Window not ready yet, wait more
			                        delay 1.5
			                    end if
			                on error
			                    -- If we can't check, wait a bit more to be safe
			                    delay 1.0
			                end try
			                
			                -- Find the message body field and type the text
			                try
			                    -- Method 1: Try to find and click the body text field
			                    set bodyField to first text area of window 1
			                    click bodyField
			                    delay 0.5
			                    keystroke plainTextBody
			                on error
				            -- Method 2: Just type at the current focus (should be body if window just opened)
				            delay 0.5
				            keystroke plainTextBody
			                end try
			            end tell
			        end tell
			        
			        -- Wait longer for typing to complete and be processed by Outlook
			        -- Longer delay ensures all keystrokes are fully processed before saving
			        delay 2.0
			    end if
			on error e
			    return "Error setting content via UI: " & e
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
			
			-- Wait before saving to ensure content is set
			delay 1.0
			
			-- 5. Save and Close (window opens automatically on creation)
			-- We must close 'window 1' assuming the new draft is focused.
			try
			    close window 1 saving yes
			on error
			    -- Fallback: try closing the message itself if supported in future
			    try 
			        save newDraft
			        close newDraft
			    on error
			    end try
			end try
			
			return "Success: Draft created."
			
		on error errMsg
			return "Error: " & errMsg
		end try
	end tell
end run
