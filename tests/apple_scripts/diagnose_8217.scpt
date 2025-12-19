on run argv
	set msgID to 8217
	
	tell application "Microsoft Outlook"
		try
			set output to "--- DEEP DIAGNOSTIC 8217 ---\n"
			
			-- 1. Inspect Target Message
			set targetMsg to message id msgID
			set output to output & "Target ID: " & (id of targetMsg) & "\n"
			set output to output & "Target Subject: " & (subject of targetMsg) & "\n"
			
			set s to sender of targetMsg
			set output to output & "Target Sender: " & (name of s) & " <" & (address of s) & ">\n"
			
			set output to output & "Target Recipients (To):\n"
			repeat with r in to recipients of targetMsg
			    try
			       set rName to name of r
			    on error
			       set rName to "Unknown"
			    end try
			    set rAddr to address of (get email address of r)
			    set output to output & " - " & rName & " <" & rAddr & ">\n"
			end repeat
			
			-- 2. Create Native Reply (No modifications)
			set newDraft to reply to targetMsg
			
			set output to output & "\n--- Native Reply Defaults ---\n"
			set ds to sender of newDraft
			set output to output & "Draft Sender: " & (name of ds) & " <" & (address of ds) & ">\n"
			
			set output to output & "Draft Recipients (To):\n"
			repeat with r in to recipients of newDraft
			    try
			       set rName to name of r
			    on error
			       set rName to "Unknown"
			    end try
			    set rAddr to address of (get email address of r)
			    set output to output & " - " & rName & " <" & rAddr & ">\n"
			end repeat
			
			close window 1 saving no
			
			return output
		on error errMsg
			return "Error: " & errMsg
		end try
	end tell
end run
