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
			
			try
			    set targetMsg to message id targetID
			on error
			    set searchFolders to {"Inbox", "Sent Items", "Archive", "Deleted Items"}
			    repeat with fName in searchFolders
			        try
			            set f to folder fName of default account
			            set targetMsg to (first message of f where id is targetID)
			            exit repeat
			        on error
			        end try
			    end repeat
			end try
			
			if targetMsg is missing value then
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
			
			-- 2. Create Reply
			set newDraft to reply to targetMsg
			
			-- Wait for draft window to fully open
			delay 2.0
			
			-- 2.1 Set Content - FIX ATTEMPT 4: UI Automation (keystrokes)
			try
			    if responseBody is not "" then
			        -- Convert HTML <br> to newlines for typing
			        set AppleScript's text item delimiters to "<br>"
			        set textItems to text items of responseBody
			        set AppleScript's text item delimiters to return
			        set plainTextBody to textItems as string
			        set AppleScript's text item delimiters to ""
			        
			        -- Use System Events to type the text
			        tell application "System Events"
			            tell process "Microsoft Outlook"
			                -- Activate the window
			                set frontmost to true
			                delay 0.5
			                
			                -- Find the message body field (usually the first text field in the window)
			                -- Try to click in the body area and type
			                try
			                    -- Method 1: Try to find and click the body text field
			                    set bodyField to first text area of window 1
			                    click bodyField
			                    delay 0.3
			                    keystroke plainTextBody
			                on error
				            -- Method 2: Just type at the current focus (should be body if window just opened)
				            keystroke plainTextBody
			                end try
			            end tell
			        end tell
			        
			        -- Wait for typing to complete
			        delay 1.0
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
			    try
			        set draftAccount to account of newDraft
			        set myAddress to email address of draftAccount
			        set myName to name of draftAccount
			    on error
			    end try
			end try
			
			-- 2.5 CLEANUP: Remove "Me" from recipients
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
			
			-- 5. Save and Close
			try
			    close window 1 saving yes
			on error
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

