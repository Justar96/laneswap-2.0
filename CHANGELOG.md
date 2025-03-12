# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2025-03-12

### Added
- New terminal monitor feature with colorful ASCII-style interface
- Terminal-based UI for monitoring service status
- Improved error handling for MongoDB adapter with index conflict resolution
- Mock API server for testing and demonstration purposes
- Enhanced logging for better troubleshooting
- Non-terminal mode for headless environments
- Auto-detection of terminal availability
- Scroll preservation in terminal monitor to avoid interrupting user navigation
- Pause/resume functionality with spacebar for uninterrupted viewing
- Command-line option to start monitor in paused mode
- Stable terminal UI with consistent display and window resize handling
- Priority-based service sorting (critical first, then warning, healthy, unknown)
- Adaptive display that shows the most important services first

### Changed
- Replaced web monitor with terminal monitor for a more lightweight approach
- Updated heartbeat system to use terminal monitor for validation
- Fixed return type of send_heartbeat method to match test expectations
- Improved MongoDB adapter initialization with better error handling
- Enhanced terminal monitor to handle different API response formats
- Refined terminal monitor refresh graphics for consistent display
- Added responsive design to terminal monitor for different terminal sizes
- Improved terminal UI to preserve scroll history and user interaction
- Fixed terminal UI stacking issues for a more stable display

### Removed
- Web monitor feature (replaced with terminal monitor)
- Web dashboard and related dependencies

## [0.1.1] - 2025-03-15

### Added
- System validation feature to verify installation
- New CLI command for manual validation
- Automatic validation during service registration
- Improved error handling for web monitor
- Added "all" extra in setup.py for easy installation of all dependencies

### Fixed
- Web monitor endpoint compatibility issues
- Dependency problems with optional packages
- Improved documentation for troubleshooting

## [0.1.0] - 2025-03-12

### Added
- Initial release of LaneSwap
- Core heartbeat monitoring system
- MongoDB adapter for persistent storage
- Discord webhook adapter for notifications
- FastAPI server for API access
- Web dashboard for monitoring
- CLI interface for management
- Async client for easy integration
- Comprehensive test suite
- Documentation and examples 