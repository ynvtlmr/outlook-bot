-- Returns recipient email and date pairs from Sent Items for stage detection.
-- Output format: one "email|YYYY-MM-DD HH:MM:SS" pair per line.
-- Scans last 1000 sent messages (newest first).
on run argv
	tell application "Microsoft Outlook"
		try
			set sentFolder to folder "Sent Items" of default account
			set msgCount to count of messages of sentFolder
			set scanLimit to 1000
			if msgCount < scanLimit then set scanLimit to msgCount

			set resultList to ""

			repeat with i from 1 to scanLimit
				try
					set msg to message i of sentFolder
					set sentDate to time sent of msg
					set dateStr to my formatDate(sentDate)
					set allRecips to to recipients of msg
					repeat with r in allRecips
						try
							set recipAddr to address of (get email address of r)
							set resultList to resultList & recipAddr & "|" & dateStr & linefeed
						end try
					end repeat
				end try
			end repeat

			return resultList
		on error errMsg
			return ""
		end try
	end tell
end run

on formatDate(d)
	set y to year of d as string
	set m to month of d as integer
	set dy to day of d
	set h to hours of d
	set mn to minutes of d
	set s to seconds of d

	set m to text -2 thru -1 of ("0" & (m as string))
	set dy to text -2 thru -1 of ("0" & (dy as string))
	set h to text -2 thru -1 of ("0" & (h as string))
	set mn to text -2 thru -1 of ("0" & (mn as string))
	set s to text -2 thru -1 of ("0" & (s as string))

	return y & "-" & m & "-" & dy & " " & h & ":" & mn & ":" & s
end formatDate
