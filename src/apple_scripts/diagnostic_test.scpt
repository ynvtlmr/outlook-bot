on run argv
    set testType to item 1 of argv
    set payload to ""
    if (count of argv) > 1 then
        set payload to item 2 of argv
    end if
    
    tell application "Microsoft Outlook"
        try
            -- Create a blank new draft
            set newDraft to make new outgoing message with properties {subject:"Outlook Bot Diagnostic: " & testType}
            
            -- Wait a beat to ensure object creation?
            delay 0.5
            
            if testType is "readback" then
                -- WRITE
                set content of newDraft to payload
                -- READ BACK IMMEDIATELY
                set storedContent to content of newDraft
                
                -- Cleanup
                close window 1 saving no -- Assuming it opens and focuses window 1
                return storedContent
                
            else if testType is "html" then
                -- Try setting HTML content specifically if that's a property, or just content containing tags
                -- Outlook usually treats 'content' as plain text unless 'html content' is used
                -- But our bot uses 'content'. Let's test that exact path.
                set content of newDraft to payload
                delay 1
                set storedContent to content of newDraft
                 -- Cleanup
                close window 1 saving no
                return storedContent
                
            else if testType is "append" then
                -- SIMULATE REPLY: Create with content, then Read-Modify-Write
                set content of newDraft to "Original Signature"
                delay 0.5
                
                -- Read back
                set oldContent to content of newDraft
                
                -- Prepend (Simulating the reply logic)
                set newContent to payload & "<br>" & oldContent
                set content of newDraft to newContent
                delay 0.5
                
                set storedContent to content of newDraft
                
                -- Cleanup
                close window 1 saving no
                return storedContent
                
            else if testType is "object_save" then
                -- TEST: Save via Object Reference (avoiding 'window 1')
                set content of newDraft to payload
                delay 0.5
                
                -- Try direct object manipulation
                save newDraft
                -- We won't close it immediately so we can read it back to verify, 
                -- or we assume 'save' worked.
                -- Let's read back to be sure it took.
                set storedContent to content of newDraft
                
                -- Now try closing object directly
                try
                    close newDraft saving yes
                on error
                    -- Some versions of Outlook don't support 'close message', must use window
                    close window 1 saving yes
                end try
                
                return storedContent
                
            else
                -- Standard write
                set content of newDraft to payload
                delay 0.5
                set storedContent to content of newDraft
                
                -- Cleanup
                close window 1 saving no
                return storedContent
            end if
            
        on error errMsg
            return "Error: " & errMsg
        end try
    end tell
end run
