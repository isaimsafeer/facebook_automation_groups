# Facebook Message Tracking System Fixes

This package contains fixes for several issues with the Facebook message tracking system:

## Issues Fixed

1. **Negative Carry Forward Messages Count**
   - Problem: The carry forward messages count decreases to negative values when messages are limited by Facebook
   - Fix: Prevents count from going negative, recalculates based on actual pending profiles

2. **Profiles Visited Exceeding Profiles Fetched**
   - Problem: Visited profiles count exceeds fetched profiles count because profiles are revisited and counted multiple times
   - Fix: Only counts unique profile visits, ensures visited never exceeds fetched

3. **Inaccurate Response Counting**
   - Problem: System notifications are incorrectly counted as responses causing inflated numbers
   - Fix: Validates message content before counting as a response

## Fix Scripts

### 1. `fix_script.py`
This script fixes the existing data in Summary-table.csv to correct the issues:
- Resets negative carry forward messages count to a valid value
- Corrects profiles visited count to not exceed profiles fetched
- Adjusts unreasonably high response counts to more realistic values

To run:
```
python fix_script.py
```

### 2. `time_tracker_updates.py` 
This script modifies the source code to prevent these issues from happening in the future:
- Updates time_tracker.py to prevent negative values
- Updates fb/auto.py to properly validate notification messages
- Adds consistency checks to ensure counts remain valid

To run:
```
python time_tracker_updates.py
```

## Usage Instructions

1. First, make sure the Facebook automation is not running
2. Run `fix_script.py` to correct the existing data
3. Run `time_tracker_updates.py` to update the code for future runs
4. Restart the application to apply all changes

## Backup
Both scripts automatically create backups of any files they modify with timestamps in the filename. If any issues occur, you can restore from these backups.

## Notes
- After applying these fixes, the message tracking system will maintain more accurate counts
- The carry forward counts will never be negative
- Only unique profiles will be counted for visits
- Only actual responses will be counted, not system notifications

If you encounter any issues after applying these fixes, please restore from the backups and contact the development team. 