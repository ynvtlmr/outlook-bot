-- Returns a newline-separated list of all recipient email addresses from Sent Items.
-- Used to check who has already been emailed (much faster than per-lead lookups).
on run argv
	tell application "Microsoft Outlook"
		try
			set sentFolder to folder "Sent Items" of default account
			set allMessages to messages of sentFolder
			set msgCount to count of allMessages
			-- Cap to last 1000 messages for performance
			if msgCount > 1000 then
				set msgCount to 1000
			end if

			set addressList to ""

			repeat with i from 1 to msgCount
				try
					set msg to item i of allMessages
					set allRecips to (to recipients of msg) & (cc recipients of msg)
					repeat with r in allRecips
						try
							set recipAddr to address of (get email address of r)
							set addressList to addressList & recipAddr & linefeed
						end try
					end repeat
				end try
			end repeat

			return addressList
		on error errMsg
			return ""
		end try
	end tell
end run
