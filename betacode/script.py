# coding=UTF-8
import betacode.greek as greek
import betacode.hebrew as hebrew
import click


@click.command()
@click.option('-h', is_flag=True, help='Hebrew betacode(defaut is Greek)')
@click.argument('filename', default='-', type=click.File('r'))
def main(h, filename):
    decode = hebrew.decode if h else greek.decode
    click.echo(decode(filename.read()))
