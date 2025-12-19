on run argv
	set msgID to 4743
	
	tell application "Microsoft Outlook"
		try
			set output to "DEBUG LOG:\n"
			
			-- 1. Find message
			set targetMsg to message id msgID
			if targetMsg is missing value then return "Msg not found"
			
			set msgSender to sender of targetMsg
			set msgSubject to subject of targetMsg
			set output to output & "Target Msg Subject: " & msgSubject & "\n"
			set output to output & "Target Msg Sender: " & name of msgSender & " <" & address of msgSender & ">\n"
			
			-- 2. Create Reply
			set newDraft to reply to targetMsg
			
			-- 3. Get 'My' Address
			set myName to ""
			set myAddress to ""
			
			try
			    set draftSender to sender of newDraft
			    set myName to name of draftSender
			    set myAddress to address of draftSender
			    set output to output & "Draft Sender: " & myName & " <" & myAddress & ">\n"
			on error
			    set output to output & "Error getting sender.\n"
			end try
			
			-- 4. Check Original Recipients
			set origTo to to recipients of targetMsg
			
			set output to output & "--- Comparisons ---\n"
			
			repeat with r in origTo
			    try
			        set rAddress to address of (get email address of r)
			        set rName to "Unknown" -- skip naming for now
			    
			        set matchStr to "NO MATCH"
			        if rAddress is equal to myAddress then
			            set matchStr to "MATCH (Exact)"
			        end if
			    
			        set output to output & "Recipient <" & rAddress & "> vs Me <" & myAddress & "> -> " & matchStr & "\n"
			    on error e
			         set output to output & "Error reading recipient: " & e & "\n"
			    end try
			end repeat
			
			
			close window 1 saving no
			return output
			
		on error errMsg
			return "Error: " & errMsg
		end try
	end tell
end run
