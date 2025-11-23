# Quick Start Guide

## Setup (First Time)

### 1. Install Dependencies

```bash
cd route-stories
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

You need:
- **Google Maps API Key**: Get from [Google Cloud Console](https://console.cloud.google.com/google/maps-apis)
  - Enable the "Directions API"
- **Anthropic API Key**: Get from [Anthropic Console](https://console.anthropic.com/)

### 3. Verify Setup

```bash
# Check that all dependencies are installed
python -c "import anthropic, googlemaps; print('Dependencies OK')"

# Check that .env file exists
test -f .env && echo ".env file exists" || echo "ERROR: .env file missing"
```

## Running the Application

### Basic Usage (Interactive Mode)

```bash
python main.py
```

You'll be prompted to enter:
1. Starting location (e.g., "Tel Aviv, Israel")
2. Destination (e.g., "Jerusalem, Israel")

Then press Enter to progress through each waypoint.

### Command-Line Arguments

```bash
# Specify route directly
python main.py --start "Tel Aviv" --end "Jerusalem"

# Process only first 3 waypoints
python main.py --start "Tel Aviv" --end "Jerusalem" --max-points 3

# Enable verbose logging
python main.py --start "Tel Aviv" --end "Jerusalem" --verbose

# Export results to custom location
python main.py --start "Tel Aviv" --end "Jerusalem" --export results.json
```

## What to Expect

1. **Route Planning**: The system fetches your route from Google Maps
2. **For Each Waypoint**:
   - Video Agent searches for relevant YouTube videos
   - Song Agent searches for related music
   - Story Agent finds historical facts
   - Judge Agent evaluates all three and selects the best content
3. **Results**: View selected content with explanations
4. **Export**: Results are automatically saved to JSON

## Example Session

```
$ python main.py --start "Tel Aviv" --end "Jerusalem" --max-points 3

================================================================================
                         ROUTE STORIES
               AI-Powered Journey Content Curator
================================================================================

Route: Tel Aviv → Jerusalem

Fetching route from Google Maps...

================================================================================
ROUTE INFORMATION
================================================================================
From: Tel Aviv, Israel
To: Jerusalem, Israel
Total Distance: 63.5 km
Estimated Duration: 52 minutes
Waypoints: 3
================================================================================

--------------------------------------------------------------------------------
WAYPOINT 1 of 3
--------------------------------------------------------------------------------
Location: Tel Aviv, Israel
Coordinates: 32.085300, 34.781768
--------------------------------------------------------------------------------

Searching for content about: Tel Aviv, Israel
This may take a moment...

Agents working:
  [*] Video Agent - searching YouTube...
  [*] Song Agent - searching music...
  [*] Story Agent - searching historical facts...
  [*] Judge Agent - evaluating options...

================================================================================
RESULTS
================================================================================

✓ SELECTED CONTENT: SONG
--------------------------------------------------------------------------------
Title: Streets of Tel Aviv
Artist: Local Artists Collective
Genre: Folk
Duration: 3:45
Album: Sounds of Tel Aviv
URL: https://spotify.com/track/mock_song_1

Judge's Reasoning: This song captures the vibrant atmosphere of Tel Aviv...
Confidence Score: 85/100
================================================================================

--------------------------------------------------------------------------------
Press Enter to continue to next waypoint (or 'q' to quit):
```

## Troubleshooting

### "Error loading configuration"
- Make sure you created the `.env` file
- Check that API keys are set correctly (no quotes needed)

### "Failed to get route from Google Maps"
- Verify your Google Maps API key is valid
- Ensure Directions API is enabled in Google Cloud Console
- Check that location names are spelled correctly

### "Claude API call failed"
- Verify your Anthropic API key is valid
- Check your API quota/credits

### Import Errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Use Python 3.8 or higher

## Output Files

- **Logs**: `logs/route_stories_TIMESTAMP.log`
- **Results**: `output/route_ROUTEID.json`

## Next Steps

Once you have the basic system working:
1. Customize agent prompts in `agents/` directory
2. Add real YouTube/Spotify API integration in `services/search_tools.py`
3. Implement timer-based progression in `core/scheduler.py`
4. Add web UI using Flask/FastAPI
5. Implement result caching for repeated routes

## Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Review the assignment documentation
3. Consult the code comments in each module
