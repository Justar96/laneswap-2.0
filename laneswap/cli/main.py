from .commands import start_server, monitor_link

@click.group()
def cli():
    """LaneSwap CLI tools."""
    pass

cli.add_command(start_server)
cli.add_command(monitor_link)

if __name__ == '__main__':
    cli() 