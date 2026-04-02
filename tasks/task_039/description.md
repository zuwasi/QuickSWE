# Bug Report: App Stops Responding After Several Hours

## Summary
The application stops responding after running for a few hours under normal load. Restarting the service fixes it temporarily. No obvious errors in the logs — the app just hangs on database operations.

## Steps to Reproduce
1. Run the application under sustained load
2. Wait 3-6 hours (faster under higher load)
3. Application becomes unresponsive on any DB operation
4. Thread dump shows all threads waiting to acquire a connection

## Environment
- Python 3.11
- Custom connection pool (max_size=10)
- Retry policy enabled with 3 retries

## Additional Notes
- The retry module was added recently for fault tolerance
- Thread dump shows all connections are "in use" but none active
- Memory usage is stable — not a memory leak
- Might be related to the new retry logic? Or the transaction manager?
- We've tried increasing pool size but it only delays the problem
