from core.scheduler import Scheduler
import click


@click.command()
@click.option('--metric', type=click.Choice(['cpu', 'mem','processes']), help='Add a metric (cpu、mem or processes)')
def _main(metric):
    s = Scheduler(metric)
    s.start()


if __name__ == '__main__':
    _main()
