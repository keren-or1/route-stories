# Route Stories - Web UI Documentation

## Overview

The Route Stories Web UI provides a modern, professional interface for interacting with the multi-agent route content curation system. Built with Flask, it offers real-time progress tracking, comprehensive results display, and an intuitive user experience.

## Features

### 1. Home Page (/)
- **Route Input Form**: Enter start location, end location, and maximum waypoints
- **Interactive Slider**: Adjust waypoints count (2-20) with visual feedback
- **How It Works**: Educational section explaining the system
- **Content Types**: Overview of videos, songs, and stories
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile

### 2. Processing Page (/processing/<route_id>)
- **Real-time Progress**: Live progress bar showing waypoint completion
- **Current Waypoint**: Display of the waypoint being processed
- **Agent Status**: Visual indicators for Video, Song, Story, and Judge agents
- **Elapsed Time**: Live timer showing processing duration
- **Error Tracking**: Display of any errors that occur during processing

### 3. Results Page (/results/<route_id>)
- **Route Summary**: Complete overview of processed route
- **Statistics Dashboard**: Total waypoints, content distribution, average scores
- **Waypoint Cards**: Detailed view of each waypoint with:
  - Selected content (video/song/story)
  - Judge's reasoning and score
  - All candidate options with visual indicators
  - Links to external content
- **Export Functionality**: Download results as JSON
- **New Route**: Easy navigation to start a new route

## Architecture

### Backend Structure
```
src/web/
├── __init__.py          # Package initialization
├── app.py               # Flask application factory
├── routes.py            # URL routes and API endpoints
├── static/              # Static assets
│   ├── css/
│   │   └── style.css    # Professional styling
│   └── js/
│       └── main.js      # Frontend functionality
└── templates/           # HTML templates
    ├── base.html        # Base template with navigation
    ├── index.html       # Home page
    ├── processing.html  # Processing progress page
    ├── results.html     # Results display page
    └── error.html       # Error page
```

### API Endpoints

#### POST /api/process-route
Start processing a new route.

**Request:**
```json
{
  "start": "New York, NY",
  "end": "Boston, MA",
  "max_points": 5
}
```

**Response:**
```json
{
  "route_id": "uuid-here",
  "total_waypoints": 5,
  "origin": "New York, NY",
  "destination": "Boston, MA"
}
```

#### GET /api/progress/<route_id>
Get real-time progress for a route.

**Response:**
```json
{
  "route_id": "uuid-here",
  "status": "processing",
  "current_waypoint": 3,
  "total_waypoints": 5,
  "progress_percentage": 60,
  "elapsed_time": 45,
  "current_waypoint_info": {
    "point_id": 2,
    "address": "Hartford, CT"
  },
  "errors": []
}
```

#### GET /api/results/<route_id>
Get final results for a completed route.

**Response:**
```json
{
  "route_id": "uuid-here",
  "total_waypoints": 5,
  "waypoints": [...],
  "statistics": {
    "total_waypoints": 5,
    "content_type_distribution": {
      "video": 2,
      "song": 2,
      "story": 1,
      "error": 0
    },
    "average_judge_score": 85.4,
    "total_errors": 0
  }
}
```

## Running the Web UI

### 1. Installation

Install Flask dependency:
```bash
cd route-stories
pip install -r requirements.txt
```

### 2. Configuration

Ensure your `.env` file contains:
```
GOOGLE_MAPS_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

### 3. Start the Server

**Option A: Using web_main.py**
```bash
python src/web_main.py
```

**Option B: Using Flask CLI**
```bash
export FLASK_APP=src/web/app.py
flask run
```

**Option C: Direct Python**
```bash
python -c "from src.web import create_app; create_app().run(debug=True)"
```

### 4. Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

## User Guide

### Creating a Route

1. **Navigate to Home Page**: Open http://localhost:5000
2. **Enter Route Details**:
   - Starting Location: e.g., "New York, NY"
   - Destination: e.g., "Boston, MA"
   - Maximum Waypoints: Use slider to select (2-20)
3. **Submit**: Click "Start Journey" button
4. **Processing**: You'll be redirected to the processing page

### Monitoring Progress

The processing page shows:
- **Progress Bar**: Visual indicator of completion
- **Current Waypoint**: Location being processed
- **Agent Status**: Real-time status of all agents
- **Elapsed Time**: How long processing has taken
- **Errors**: Any issues that occur

The page automatically updates every second and redirects to results when complete.

### Viewing Results

The results page displays:
- **Statistics**: Overview of the route processing
- **Waypoint Cards**: Each waypoint shows:
  - Location and coordinates
  - Selected content (highlighted with icon)
  - Judge's score and reasoning
  - All candidate options (video, song, story)
  - Links to external content

### Exporting Results

Click the "Export Results" button to download a JSON file containing:
- All waypoint data
- Selected content for each location
- Judge decisions and reasoning
- Statistics and metadata

## Design System

### Color Scheme
- **Primary**: #4F46E5 (Indigo) - Main brand color
- **Secondary**: #06B6D4 (Cyan) - Accents
- **Success**: #10B981 (Green) - Positive actions
- **Danger**: #EF4444 (Red) - Errors
- **Background**: #F9FAFB (Light Gray)

### Typography
- **Font Family**: System fonts (-apple-system, BlinkMacSystemFont, Segoe UI, Roboto)
- **Base Size**: 16px
- **Headings**: Bold, larger sizes with gradient effects

### Components

#### Cards
- White background with subtle shadow
- Rounded corners (0.75rem)
- Padding for comfortable spacing
- Hover effects for interactivity

#### Buttons
- Primary: Gradient blue with hover animations
- Secondary: Gray with subtle hover
- Loading states with spinners
- Disabled states for form validation

#### Progress Indicators
- Animated progress bars
- Agent status badges (pending, running, completed)
- Elapsed time counter
- Percentage display

#### Content Icons
- 🎥 Video content
- 🎵 Song content
- 📖 Story content
- ⚖️ Judge decisions
- 🗺️ Route/waypoint markers

## Responsive Design

### Breakpoints
- **Desktop**: > 768px - Full layout with grid
- **Tablet**: 481-768px - Adjusted grid, stacked navigation
- **Mobile**: ≤ 480px - Single column, optimized touch targets

### Mobile Optimizations
- Touch-friendly button sizes
- Readable font sizes
- Simplified layouts
- Reduced padding for space efficiency
- Collapsible sections

## Performance

### Frontend Optimizations
- Efficient DOM manipulation
- Debounced input validation
- Minimal JavaScript dependencies
- CSS animations for smooth transitions
- Local storage for recent routes

### Backend Optimizations
- Background threading for route processing
- Session-based state management
- Efficient JSON serialization
- Connection pooling for APIs
- Graceful error handling

## Troubleshooting

### Common Issues

**1. Server won't start**
- Check that Flask is installed: `pip install flask`
- Verify `.env` file exists with API keys
- Ensure port 5000 is not in use

**2. Processing hangs**
- Check API key validity
- Verify Google Maps API is enabled
- Check network connectivity
- Review logs in `logs/` directory

**3. Results not displaying**
- Ensure route processing completed
- Check browser console for errors
- Verify route_id is valid
- Clear browser cache if needed

**4. Styling issues**
- Clear browser cache
- Check that static files are served correctly
- Verify CSS file exists at `/static/css/style.css`

### Debug Mode

Enable Flask debug mode for detailed errors:
```python
app.run(debug=True)
```

Check application logs:
```bash
tail -f logs/route_stories.log
```

## Production Deployment

### WSGI Server

Use Gunicorn for production:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "src.web:create_app()"
```

### Environment Variables
```bash
export FLASK_ENV=production
export SECRET_KEY=your-secret-key-here
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/route-stories/src/web/static;
    }
}
```

### Security Considerations
- Set strong `SECRET_KEY` in production
- Use HTTPS for secure connections
- Implement rate limiting
- Add CSRF protection
- Validate all user inputs
- Sanitize outputs

## Browser Support

### Tested Browsers
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Required Features
- ES6 JavaScript
- CSS Grid and Flexbox
- Fetch API
- Local Storage
- CSS Custom Properties

## Accessibility

### Features
- Semantic HTML5 elements
- ARIA labels for screen readers
- Keyboard navigation support
- High contrast color scheme
- Responsive text sizing
- Focus indicators

### Standards
- WCAG 2.1 Level AA compliance
- Mobile accessibility
- Screen reader compatible

## Future Enhancements

Potential improvements:
- User authentication and saved routes
- Route sharing via URL
- Map visualization with Google Maps embed
- Content preview in results
- Advanced filtering and search
- Route comparison
- PDF export
- Dark mode toggle
- Multi-language support
- Route recommendations

## Support

For issues or questions:
1. Check this documentation
2. Review application logs
3. Check browser console
4. Verify API configuration
5. Test with simple routes first

## License

Part of the Route Stories project.
