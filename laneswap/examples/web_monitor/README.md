# LaneSwap Web Monitor

This is a web-based dashboard for monitoring LaneSwap services. It provides a real-time view of service health and status.

## Features

- Real-time monitoring of service health
- Grid and table views
- Filtering and search
- Detailed service information
- Automatic refresh
- Dark/light theme support
- Internationalization (English and Thai)

## Usage

The web monitor can be started in several ways:

1. Using the CLI:
   ```bash
   laneswap dashboard --port 8080 --api-url http://localhost:8000
   ```

2. Using the standalone script:
   ```bash
   python -m laneswap.examples.start_monitor --port 8080 --api-url http://localhost:8000
   ```

3. From Python code:
   ```python
   from laneswap.examples.web_monitor.launch import start_dashboard
   start_dashboard(port=8080, api_url="http://localhost:8000")
   ```

## Accessing the Monitor

Once started, the monitor can be accessed at:
- http://localhost:8080/
- http://127.0.0.1:8080/
- http://YOUR_IP_ADDRESS:8080/

## Customization

The monitor can be customized by modifying the following files:
- `index.html` - Main HTML structure
- `styles.css` - CSS styling
- `script.js` - JavaScript functionality
- `i18n.js` - Internationalization support

## Adding New Languages

To add a new language:

1. Add a new language object to the `translations` object in `i18n.js`
2. Follow the same structure as the existing languages
3. Add a language selector button in `index.html`

## Technical Details

The web monitor is a static HTML/CSS/JavaScript application that communicates with the LaneSwap API to fetch service data. It uses:

- Bootstrap 5 for styling
- Bootstrap Icons for icons
- Vanilla JavaScript for functionality 