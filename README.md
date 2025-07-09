# Facebook Automation Tool

This tool automates the process of searching for university groups on Facebook, finding profiles, and sending messages to matching profiles.

## Features

- Searches for university groups on Facebook
- Finds profiles in these groups
- Matches profiles based on studies/university
- Sends messages to matching profiles
- Tracks metrics for each session
- Saves profiles for later processing
- Processes pending messages automatically

## Terminal Logging System

The application now includes a comprehensive terminal logging system that:

1. **Captures all terminal output**: All console output is automatically saved to log files
2. **Creates session-specific logs**: Each session gets its own log file named with timestamp and username
3. **Stores logs in organized directory**: All logs are stored in the `logs` directory
4. **Captures pending message processing**: A separate log file is created for pending message processing
5. **Handles program termination gracefully**: Log files are properly closed when the program ends

### Log File Locations

- **Session logs**: `logs/session_[TIMESTAMP]_[USERNAME].log`
- **Pending processing logs**: `logs/pending_processing_[TIMESTAMP].log`

### Accessing Logs

You can find all log files in the `logs` directory. These logs provide detailed information about what happened during each automation session, including:

- All search operations
- Profile visits
- Message sending attempts
- Errors encountered
- Metrics collected

## Setup

1. Install Python 3.7+ and the required packages:
```
pip install -r requirements.txt
```

2. Create an `account.csv` file with your Facebook login credentials:
```
username,password
your_email@example.com,your_password
```

3. Create a CSV file with university names to search for (or use the default).

## Usage

Run the main script:
```
python -m fb.auto
```

## Metrics

The tool keeps track of various metrics to help you monitor performance:

- Profiles fetched
- Profiles visited
- Profiles matched
- Messages sent
- Deleted users
- Responses received
- Already sent messages
- Carry forward profiles and messages

These metrics are saved to `Summary-table.csv` for analysis.

## Troubleshooting

If you encounter issues:

1. Check the log files in the `logs` directory
2. Ensure your Facebook credentials are correct
3. Make sure you have a stable internet connection

# Facebook Messaging System

## University File Format

The system requires a CSV file with university names. The file must have the following format:

### Required Format
- CSV file format
- Must have a column named `university` containing the university names
- Example:

```csv
university
University of Oxford
University of Cambridge
Imperial College London
```

### Troubleshooting

If your university file is not being accepted:

1. **Check the column name**: The file must have a column named exactly "university".
2. **Check the file format**: Make sure it's a proper CSV file with comma separators.
3. **Check for empty lines**: Remove any blank lines in the file.
4. **Use the template**: You can download a template file from the upload page.

### Auto-Repair

The system will attempt to fix common issues with university files:
- If the file has a single column but it's not named "university", it will be renamed
- If the file has multiple columns, it will try to find a column that has "uni" in its name
- If no suitable column is found, it will use the first column
- If CSV parsing fails, it will try to extract university names line by line

## Additional Information

The system stores university files at:
- `main/staticfiles/sessions/uniall.csv` (when running through Django)
- `staticfiles/uni_list1.csv` (alternative location for standalone mode)

When running standalone, if no university file is found, a default list with popular universities will be created automatically. 