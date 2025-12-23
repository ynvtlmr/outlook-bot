on run
	tell application "Microsoft Outlook"
		try
			set draftFolder to folder "Drafts" of default account
			-- Get all messages
			set allDrafts to messages of draftFolder
			
			if (count of allDrafts) is 0 then
				return "Error: No drafts found."
			end if
			
			-- Find the one with the latest modification time
			set latestMsg to item 1 of allDrafts
			set latestTime to time sent of latestMsg -- 'time sent' for draft is creation/mod time often?
			-- Actually for drafts 'time sent' might be missing or old. 'creation time'? -> 'time received' is creation time for draft usually.
			-- Let's try to assume the 'first message' is the newest if sorted? Outlook sorting varies.
			-- Let's sort by ID manually? IDs are increasing? 
			
			-- Use a simple robust comparison loop
			set latestMsg to missing value
			set latestDate to date "1/1/1900"
			
			repeat with msg in allDrafts
			    -- For drafts, 'time sent' seems to be the creation/mod time, but may be missing
			    set msgDate to missing value
			    try
			        set msgDate to time sent of msg
			    on error
			        -- Some drafts may not have 'time sent'; try 'time received' as a fallback
			        try
			            set msgDate to time received of msg
			        on error
			            -- If neither timestamp is available, skip this draft
			            set msgDate to missing value
			        end try
			    end try
			    
			    if msgDate is not missing value then
			        if msgDate > latestDate then
			            set latestDate to msgDate
			            set latestMsg to msg
			        end if
			    end if
			end repeat
			
			if latestMsg is missing value then
			    -- Fallback
			    return "Error: Could not determine latest draft."
			end if
			
			-- Return the content
			return content of latestMsg
			
		on error errMsg
			return "Error: " & errMsg
		end try
	end tell
end run
