# Telegram Conference Contacts Tracker

Automatically track new Telegram connections made at conferences (via QR code scans) and export them to Google Sheets with AI-powered company extraction.

## Features

- **Automatic Contact Detection**: Monitors incoming private messages to detect new 1-on-1 conversations
- **AI-Powered Extraction**: Uses GPT-4 to extract company name, role, and topics from user bios and messages
- **Google Sheets Integration**: Automatically logs all contact information to a structured spreadsheet
- **Bot Commands**: Manual management tools for tagging, editing, and exporting contacts
- **Local Database**: SQLite cache for fast lookups and offline capability
- **Confirmation Messages**: Get notified in Saved Messages when new contacts are logged

## Prerequisites

- **Python 3.8+**: Required for asyncio and modern Python features
- **Telegram Account**: Personal account (not a bot) for scanning QR codes
- **Google Cloud Project**: For Google Sheets API access
- **OpenAI API Key**: For GPT-4 powered information extraction

## Installation

### 1. Clone or Download

```bash
cd telegram_contacts_tracker
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### 1. Get Telegram API Credentials

1. Go to [https://my.telegram.org/apps](https://my.telegram.org/apps)
2. Log in with your phone number
3. Click on "API development tools"
4. Create a new application (if you haven't already)
   - App title: "Conference Contacts Tracker" (or any name)
   - Short name: "contacts_tracker" (or any short name)
   - Platform: Desktop
5. Copy your `api_id` and `api_hash`

### 2. Set Up Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the **Google Sheets API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click "Enable"
4. Create a Service Account:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in the service account details
   - Click "Create and Continue"
   - Skip the optional steps and click "Done"
5. Create and Download JSON Key:
   - Click on the service account you just created
   - Go to the "Keys" tab
   - Click "Add Key" > "Create New Key"
   - Choose "JSON" format
   - Click "Create" - the JSON file will download automatically
6. Save the downloaded JSON file to your project directory
7. **Important**: Copy the service account email (it looks like `your-service@project-id.iam.gserviceaccount.com`)

### 3. Create Google Sheet (Optional)

You can either:
- **Option A**: Let the bot create the sheet automatically (requires broader permissions)
- **Option B**: Create the sheet manually:
  1. Go to [Google Sheets](https://sheets.google.com)
  2. Create a new spreadsheet named "Conference Contacts"
  3. Share it with your service account email (from step 2.7 above)
  4. Give it "Editor" permissions

### 4. Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Log in or create an account
3. Click "Create new secret key"
4. Copy the API key (you won't be able to see it again)

### 5. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your credentials:
   ```bash
   # Telegram API Credentials (from step 1)
   TELEGRAM_API_ID=12345678
   TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
   TELEGRAM_PHONE_NUMBER=+1234567890

   # OpenAI API Key (from step 4)
   OPENAI_API_KEY=sk-...

   # Google Sheets Configuration
   GOOGLE_SHEET_NAME=Conference Contacts
   GOOGLE_SERVICE_ACCOUNT_FILE=./path/to/your-service-account.json

   # Optional Settings
   DATABASE_PATH=./contacts.db
   LOG_LEVEL=INFO
   INITIAL_MESSAGES_COUNT=5
   ```

## Usage

### First Run

1. Start the bot:
   ```bash
   python main.py
   ```

2. On first run, you'll be prompted to:
   - Enter your phone number (if not in .env)
   - Enter the verification code sent to your Telegram app
   - This creates a `.session` file for future authentication

3. The bot will start monitoring for new contacts

### How It Works

1. **Automatic Tracking**: When someone new messages you:
   - The bot detects it's a first-time conversation
   - Collects user's name, username, and bio
   - Retrieves the first 5 messages for context
   - Uses GPT-4 to extract company and role
   - Saves everything to SQLite database
   - Exports to Google Sheets
   - Sends confirmation to your Saved Messages

2. **Manual Commands**: Send these commands to yourself or any chat:

   **`/tag_event <event_name> [hours]`**
   ```
   Tag contacts from the last N hours with an event name
   Example: /tag_event "ETHDenver 2024" 24
   Default: 24 hours
   ```

   **`/edit <user_id> <field> <value>`**
   ```
   Update contact information manually
   Fields: company, role, notes, event_tag
   Example: /edit 123456789 company "Solana Foundation"
   Example: /edit 123456789 notes "Discuss partnership in Q2"
   ```

   **`/export`**
   ```
   Manually trigger sync of all contacts to Google Sheets
   Useful if automatic sync fails
   ```

   **`/stats`**
   ```
   Show summary statistics:
   - Total contacts tracked
   - Contacts with identified companies
   - Recent contacts (last 7 days)
   - Breakdown by event
   ```

   **`/help`**
   ```
   Display all available commands
   ```

### Google Sheets Structure

The exported sheet has the following columns:

| Column | Description |
|--------|-------------|
| User ID | Telegram user ID (unique identifier) |
| Timestamp | When the contact was first added |
| Name | User's full name |
| Username | Telegram username (@handle) |
| Company | Extracted company name |
| Role | Extracted job title/role |
| Bio | User's Telegram bio |
| Initial Context | Topics from first messages |
| Event Tag | Conference/event name |
| Last Contact | Last time they messaged you |
| Notes | Your manual notes |

## Troubleshooting

### "Missing required environment variables"

**Solution**: Make sure your `.env` file exists and contains all required variables. Check that there are no typos in variable names.

### "Telethon FloodWaitError"

**Problem**: Telegram rate limit exceeded (too many API requests)

**Solution**: Wait for the specified time (usually a few minutes). The bot will automatically retry. To avoid this:
- Don't test the bot with too many rapid requests
- Don't run multiple instances simultaneously

### "OpenAI RateLimitError"

**Problem**: OpenAI API rate limit or quota exceeded

**Solution**:
- Wait a few minutes and the bot will retry
- Check your OpenAI account billing and limits
- Consider upgrading your OpenAI plan if you process many contacts

### "Google API Error: 403 Forbidden"

**Problem**: Service account doesn't have access to the sheet

**Solution**:
1. Find your service account email in the JSON file
2. Open your Google Sheet
3. Click "Share" and add the service account email
4. Give it "Editor" permissions

### "Could not fetch full user info"

**Problem**: Some users have privacy settings that prevent bio access

**Solution**: This is normal. The bot will still log the contact with whatever information is available. You can manually add details later with `/edit`.

### Session file errors

**Problem**: `.session` file is corrupted

**Solution**:
```bash
rm telegram_contacts_tracker.session*
python main.py  # Will prompt for phone/code again
```

### Bot doesn't detect new contacts

**Checklist**:
- Make sure the bot is running
- Verify the message is from a user (not a bot or channel)
- Check if the contact already exists in the database
- Look for errors in the console output
- Ensure LOG_LEVEL=DEBUG in .env for detailed logs

## Data Privacy & Security

### What Data is Stored

- **Telegram Profile Info**: User ID, name, username, bio
- **Message Content**: Only first 5 messages (configurable)
- **Extracted Info**: Company, role, topics (derived from above)
- **Metadata**: Timestamps, event tags, your notes

### Where Data is Stored

- **Local SQLite Database**: `contacts.db` on your machine
- **Google Sheets**: In your Google account
- **Telegram Session**: `.session` file contains auth token

### Security Best Practices

1. **Never commit** `.env`, `.session`, or service account JSON to version control
2. **Keep credentials secure**: Don't share API keys or session files
3. **Regular backups**: Export your Google Sheet periodically
4. **Access control**: Only share Google Sheet with trusted people
5. **Delete old sessions**: If you lose a device, revoke access:
   - Telegram: Settings > Privacy and Security > Active Sessions
   - Google: [Security settings](https://myaccount.google.com/security)

### Privacy Considerations

- This bot only tracks people who message you first
- Message content is only used for extraction (not stored long-term)
- All processing happens in your account (no third-party servers except APIs)
- You can delete any contact from both database and sheet anytime

## Testing Checklist

Before using in production, test these scenarios:

- [ ] Bot successfully connects to Telegram
- [ ] Bot authenticates with phone number and code
- [ ] New contact is detected when someone messages you
- [ ] User info is correctly extracted (name, username, bio)
- [ ] GPT-4 extraction returns valid company/role
- [ ] Contact is saved to SQLite database
- [ ] Contact is exported to Google Sheets
- [ ] Confirmation message appears in Saved Messages
- [ ] `/tag_event` command tags recent contacts
- [ ] `/edit` command updates contact info
- [ ] `/export` command syncs all contacts
- [ ] `/stats` command shows statistics
- [ ] Bot survives restart (session persistence)
- [ ] Existing contacts are not re-added

### Test Mode

To test without affecting your main account:

1. Use a separate Telegram account
2. Use a test Google Sheet
3. Set `LOG_LEVEL=DEBUG` for detailed logs
4. Test with friends who agree to message you

## Architecture

```
telegram_contacts_tracker/
├── main.py              # Entry point, app initialization
├── config.py            # Configuration and env validation
├── telegram_client.py   # Telegram event handlers and commands
├── sheets_manager.py    # Google Sheets operations
├── ai_extractor.py      # GPT-4 information extraction
├── database.py          # SQLite database operations
├── utils.py             # Helper functions
├── requirements.txt     # Python dependencies
├── .env                 # Your credentials (DO NOT COMMIT)
├── .env.example         # Template for environment variables
├── .gitignore           # Git ignore rules
└── README.md           # This file
```

## Contributing

This is a personal tool, but feel free to fork and customize for your needs. Some ideas for enhancements:

- Add support for group conversations
- Implement contact deduplication across events
- Add automatic follow-up reminders
- Create a web dashboard for visualizing contacts
- Support other LLMs besides GPT-4
- Add export to CRM systems (HubSpot, Salesforce, etc.)

## License

MIT License - feel free to modify and use for your own purposes.

## Acknowledgments

- [Telethon](https://github.com/LonamiWebs/Telethon) - Telegram client library
- [gspread](https://github.com/burnash/gspread) - Google Sheets Python API
- [OpenAI](https://openai.com) - GPT-4 API

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review logs with `LOG_LEVEL=DEBUG`
3. Verify all credentials are correct
4. Search for similar issues online

---

**Happy networking!** 🤝

Remember to always respect people's privacy and follow conference networking etiquette.
