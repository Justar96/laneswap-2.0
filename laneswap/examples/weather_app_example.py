#!/usr/bin/env python
"""
Example Weather App with LaneSwap heartbeat monitoring.

This example demonstrates the correct way to use LaneSwap for monitoring
a weather application service.
"""

import asyncio
import logging
import random
import time
from datetime import datetime
import sys

from laneswap.client.async_client import LaneswapAsyncClient
from laneswap.core.types import HeartbeatStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("weather-app")


class WeatherApp:
    """Simple weather app that uses LaneSwap for heartbeat monitoring."""
    
    def __init__(self, api_url="http://localhost:8000"):
        """Initialize the weather app."""
        self.api_url = api_url
        self.client = None
        self.running = False
    
    async def start(self):
        """Start the weather app with heartbeat monitoring."""
        logger.info("Starting Weather App with LaneSwap heartbeat monitoring")
        
        # Create the LaneSwap client
        self.client = LaneswapAsyncClient(
            api_url=self.api_url,
            service_name="Weather App",
            auto_heartbeat=True,  # Enable automatic heartbeats
            heartbeat_interval=30  # Send heartbeats every 30 seconds
        )
        
        # Connect to the API (this registers the service)
        await self.client.connect()
        logger.info(f"Connected to LaneSwap API with service ID: {self.client.service_id}")
        
        # Start the main app loop
        self.running = True
        await self.run()
    
    async def stop(self):
        """Stop the weather app."""
        logger.info("Stopping Weather App")
        self.running = False
        
        if self.client:
            # Send a final heartbeat
            await self.client.send_heartbeat(
                status=HeartbeatStatus.SHUTDOWN,
                message="Weather App shutting down gracefully"
            )
            
            # Close the client connection
            await self.client.close()
            logger.info("Disconnected from LaneSwap API")
    
    async def run(self):
        """Main app loop that simulates weather data processing."""
        try:
            while self.running:
                # Simulate fetching and processing weather data
                logger.info("Fetching weather data...")
                await self.fetch_weather_data()
                
                # Wait before the next update
                await asyncio.sleep(60)  # Update every minute
                
        except Exception as e:
            logger.error(f"Error in weather app: {str(e)}")
            
            # Send error heartbeat
            if self.client:
                await self.client.send_heartbeat(
                    status=HeartbeatStatus.ERROR,
                    message=f"Error in weather app: {str(e)}",
                    metadata={"error": str(e), "timestamp": time.time()}
                )
            
            # Re-raise the exception
            raise
    
    async def fetch_weather_data(self):
        """Simulate fetching and processing weather data."""
        # Simulate API call to weather service
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Simulate occasional errors
        if random.random() < 0.1:  # 10% chance of error
            if random.random() < 0.5:  # 50% of errors are warnings
                logger.warning("Weather API response slow")
                await self.client.send_heartbeat(
                    status=HeartbeatStatus.WARNING,
                    message="Weather API response slow",
                    metadata={"response_time": "5.2s", "timestamp": time.time()}
                )
            else:
                # Simulate a more serious error
                raise Exception("Failed to connect to weather API")
        
        # Process the weather data
        temperature = random.uniform(-10, 40)
        humidity = random.uniform(0, 100)
        wind_speed = random.uniform(0, 30)
        
        logger.info(f"Weather data: Temp={temperature:.1f}°C, Humidity={humidity:.1f}%, Wind={wind_speed:.1f}km/h")
        
        # Send a heartbeat with the weather data
        await self.client.send_heartbeat(
            status=HeartbeatStatus.HEALTHY,
            message="Weather data updated successfully",
            metadata={
                "temperature": round(temperature, 1),
                "humidity": round(humidity, 1),
                "wind_speed": round(wind_speed, 1),
                "updated_at": datetime.now().isoformat()
            }
        )


async def main():
    """Main entry point for the weather app."""
    app = WeatherApp()
    
    try:
        # Handle graceful shutdown
        loop = asyncio.get_running_loop()
        
        # Register signal handlers for graceful shutdown
        for signal_name in ('SIGINT', 'SIGTERM'):
            if sys.platform != 'win32' or signal_name != 'SIGTERM':
                loop.add_signal_handler(
                    getattr(signal, signal_name),
                    lambda: asyncio.create_task(app.stop())
                )
        
        # Start the app
        await app.start()
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    finally:
        # Ensure the app is stopped
        await app.stop()


if __name__ == "__main__":
    # Import signal module only if needed
    import signal
    
    # Run the app
    asyncio.run(main()) 