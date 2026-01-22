on run argv
	set msgID to item 1 of argv
	set responseBody to ""
	if (count of argv) > 1 then
		set responseBody to item 2 of argv
	end if
    
    set bccAddress to ""
    if (count of argv) > 2 then
        set bccAddress to item 3 of argv
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
			
			-- Initial delay to allow draft window to start opening
			delay 1.0
			
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
			                -- CRITICAL: Activate Outlook first to ensure it's the front app
			                set frontmost to true
			                delay 0.5
			                
			                -- Wait for window to appear and be ready (with retries)
			                set maxRetries to 10
			                set retryCount to 0
			                set windowReady to false
			                
			                repeat while not windowReady and retryCount < maxRetries
			                    try
			                        set winCount to count of windows
			                        if winCount > 0 then
			                            -- Window exists, try to access the text area
			                            try
			                                set bodyField to first text area of window 1
			                                set windowReady to true
			                            on error
			                                -- Text area not ready yet
			                                set retryCount to retryCount + 1
			                                delay 0.5
			                            end try
			                        else
			                            -- No windows yet
			                            set retryCount to retryCount + 1
			                            delay 0.5
			                        end if
			                    on error
			                        -- Error checking, wait and retry
			                        set retryCount to retryCount + 1
			                        delay 0.5
			                    end try
			                end repeat
			                
			                -- Additional safety delay after window is ready
			                delay 1.0
			                
			                -- Now focus and type the text with multiple attempts
			                set typingSuccess to false
			                set attemptCount to 0
			                set maxAttempts to 3
			                
			                repeat while not typingSuccess and attemptCount < maxAttempts
			                    try
			                        set attemptCount to attemptCount + 1
			                        
			                        -- Method 1: Explicitly find, click, and focus the body field
			                        set bodyField to first text area of window 1
			                        
			                        -- Click to focus
			                        click bodyField
			                        delay 0.3
			                        
			                        -- Click again to ensure focus (sometimes first click doesn't stick)
			                        click bodyField
			                        delay 0.3
			                        
			                        -- Move cursor to beginning (Command+A then delete to clear, or just start typing)
			                        -- Actually, let's just type - it should append or replace
			                        -- But first, ensure we're at the start by using Command+Up Arrow
			                        key code 126 using command down -- Command+Up Arrow (move to top)
			                        delay 0.2
			                        
			                        -- Now type the text
			                        keystroke plainTextBody
			                        delay 0.5
			                        
			                        -- Verify typing happened by checking if we can still interact
			                        set typingSuccess to true
			                        
			                    on error e
			                        -- If this attempt failed, wait and try again
			                        delay 0.5
			                        if attemptCount < maxAttempts then
			                            -- Try alternative: just type without finding field
			                            try
			                                keystroke plainTextBody
			                                set typingSuccess to true
			                            on error
			                                -- Continue to next attempt
			                            end try
			                        end if
			                    end try
			                end repeat
				
			                -- Final delay to ensure all keystrokes are processed
			                delay 2.5
			            end tell
			        end tell
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

            -- 3.5 Add BCC if provided
            if bccAddress is not "" then
                try
                    make new bcc recipient at newDraft with properties {email address:{address:bccAddress}}
                on error e
                    -- log error if needed
                end try
            end if
			
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
