on run argv
    set targetEmail to item 1 of argv
    set emailList to {}
    set collectedMessages to {}
    
    tell application "Microsoft Outlook"
		try
			set allInboxes to every mail folder where name is "Inbox"
			
			repeat with currentFolder in allInboxes
				try
				    set msgCount to count of messages of currentFolder
				    
				    -- Limit scan to recent 500 messages for performance
				    set scanLimit to 500
				    set startIndex to 1
				    if msgCount > scanLimit then
				        set startIndex to msgCount - scanLimit + 1
				    end if
				    
				    if msgCount > 0 then
    				    repeat with i from msgCount to startIndex by -1
    				        try
    				            set msg to message i of currentFolder
    				            set matchFound to false
    				            
    				            -- Check Sender
    				            set msgSender to sender of msg
    				            set senderAddress to address of msgSender
    				            if senderAddress contains targetEmail then
    				                set matchFound to true
    				            end if
    				            
    				            if matchFound then
    				                set end of collectedMessages to msg
    				            end if
    				            
    				        on error loopErr
    				            -- Ignore single message error
    				        end try
    				    end repeat
    				end if
					
				on error errMsg
					-- Ignore folder error
				end try
			end repeat
			
			repeat with msg in collectedMessages
				try
					set msgSender to sender of msg
					set msgSenderAddress to address of msgSender
					set msgSubject to subject of msg
					set msgContent to plain text content of msg
					set msgDate to time sent of msg
					
					set end of emailList to msgSenderAddress & "|||" & msgSubject & "|||" & msgDate & "|||" & msgContent & "///END_OF_EMAIL///"
				on error
				    -- Skip bad parse
				end try
			end repeat
			
		on error errMsg
			return "Error: " & errMsg
		end try
	end tell
    
    set AppleScript's text item delimiters to "\n"
    return emailList as text
end run
