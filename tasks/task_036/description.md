# Bug Report: Financial Reports Off by Pennies

## Summary
Financial reports show pennies off after running monthly batch processing. The totals don't add up exactly to what they should be. Sometimes it's a cent over, sometimes under. The discrepancy grows with more transactions.

## Steps to Reproduce
1. Run the monthly batch processing for any account with 50+ transactions
2. Compare the reported total with manual calculation
3. The numbers are slightly off — usually by a few cents

## Environment
- Python 3.11
- Production batch runner

## Additional Notes
- This was reported by the accounting team after Q3 close
- The tax calculation module was recently refactored — might be related?
- We also updated the ledger's summary method last sprint
- Some developers think it might be a rounding mode issue in the tax module
