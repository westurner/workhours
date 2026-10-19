"""sqlite-utils command plugin for exporting workhours source records."""

import click
import sqlite_utils

from .exporter import EXPORT_MODES, export_records
from .parsers import PARSER_MODULES, iter_records


@sqlite_utils.hookimpl
def register_commands(cli):
    @cli.command("workhours")
    @click.argument("database", type=click.Path(dir_okay=False))
    @click.argument("source_type", type=click.Choice(tuple(PARSER_MODULES)))
    @click.argument("source", type=click.Path(exists=True, dir_okay=False))
    @click.option("--table", "table_name", default="events", show_default=True)
    @click.option(
        "--mode", type=click.Choice(EXPORT_MODES), default="append", show_default=True
    )
    def workhours_export(database, source_type, source, table_name, mode):
        "Export one workhours source to a canonical SQLite table."
        try:
            with sqlite_utils.Database(database) as output_db:
                count = export_records(
                    output_db,
                    iter_records(source_type, source),
                    table_name=table_name,
                    mode=mode,
                )
        except (OSError, TypeError, ValueError, sqlite_utils.utils.sqlite3.Error) as error:
            raise click.ClickException(str(error)) from error
        click.echo("Exported {} records to {}.{}".format(count, database, table_name))