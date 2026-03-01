on run argv
	set targetEmail to item 1 of argv

	tell application "Microsoft Outlook"
		try
			set sentFolder to folder "Sent Items" of default account
			set sentMessages to messages of sentFolder

			repeat with msg in sentMessages
				try
					set toRecips to to recipients of msg
					repeat with r in toRecips
						try
							set recipAddr to address of (get email address of r)
							if recipAddr is equal to targetEmail then
								return "true"
							end if
						end try
					end repeat

					set ccRecips to cc recipients of msg
					repeat with r in ccRecips
						try
							set recipAddr to address of (get email address of r)
							if recipAddr is equal to targetEmail then
								return "true"
							end if
						end try
					end repeat

					set bccRecips to bcc recipients of msg
					repeat with r in bccRecips
						try
							set recipAddr to address of (get email address of r)
							if recipAddr is equal to targetEmail then
								return "true"
							end if
						end try
					end repeat
				end try
			end repeat

			return "false"
		on error errMsg
			return "false"
		end try
	end tell
end run
