# Bug Report: User Names Getting Cut Off

## Summary
User names are getting cut off in the database. No errors appear in the logs. The full name is submitted in the form but only a portion is stored. Discovered when a user with a long name complained their profile was wrong.

## Steps to Reproduce
1. Create a user with a name longer than 50 characters
2. Save the record
3. Retrieve the record — the name is truncated to 50 characters
4. No error was raised during the save

## Expected Behavior
Either store the full name or raise a validation error telling the user the name is too long.

## Additional Notes
- The validator module has max_length checks, so we assumed it was covered
- The serializer was refactored last month to improve performance
- We're using our custom schema/serializer — not an ORM
- Could be related to the encoding layer? Some users with unicode names also report issues
