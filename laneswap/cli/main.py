"""Main entry point for the LaneSwap CLI."""

from .commands import cli
from .service_commands import service

cli.add_command(service)

if __name__ == "__main__":
    cli() 