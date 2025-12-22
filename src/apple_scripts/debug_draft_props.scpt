on run
	tell application "Microsoft Outlook"
		try
			set draftFolder to folder "Drafts" of default account
			set allDrafts to messages of draftFolder
			if (count of allDrafts) > 0 then
				set msg to item 1 of allDrafts
				-- Return a bunch of dates to see what works
				set props to "Subject: " & subject of msg & "\n"
				try
				    set props to props & "Time Sent: " & time sent of msg & "\n"
				on error
				    set props to props & "Time Sent: ERROR\n"
				end try
				try
				    set props to props & "Time Received: " & time received of msg & "\n"
				on error
                    set props to props & "Time Received: ERROR\n"
                end try

                try
                    set props to props & "Id: " & id of msg & "\n"
                on error
                    set props to props & "Id: ERROR\n"
                end try
				return props
			else
				return "No drafts found."
			end if
		on error errMsg
			return "Error: " & errMsg
		end try
	end tell
end run
