"""Load a file written by ``export_json`` into a freshly migrated database.

    python manage.py migrate
    python manage.py flush --no-input        (empties the tables the migrations seeded)
    python manage.py import_json full-db.json

Django's own ``loaddata`` stops on this project for the same reason
``dumpdata`` does: saving a many-to-many field to a company table goes through
the company-scoped manager. This saves each company's rows inside that
company's context, all in one transaction (nothing is half-loaded), checks
every reference once at the end, and resets the id sequences so new rows
continue after the loaded ones.
"""

from django.core import serializers
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import DEFAULT_DB_ALIAS, connections, transaction

from common.models import TenantOwned
from common.tenant import use_company


def _save(item, deferred):
    instance = item.object
    company_id = getattr(instance, "company_id", None) if isinstance(instance, TenantOwned) else None
    if company_id:
        with use_company(company_id):
            item.save(using=DEFAULT_DB_ALIAS)
    else:
        item.save(using=DEFAULT_DB_ALIAS)
    if item.deferred_fields:
        deferred.append((item, company_id))


class Command(BaseCommand):
    help = "Load a JSON file from export_json into this (freshly migrated, flushed) database."

    def add_arguments(self, parser):
        parser.add_argument("file", help="The file export_json wrote.")

    def handle(self, *args, **options):
        connection = connections[DEFAULT_DB_ALIAS]
        loaded, models, deferred = 0, set(), []
        try:
            with open(options["file"], encoding="utf-8") as stream, transaction.atomic():
                with connection.constraint_checks_disabled():
                    for item in serializers.deserialize("json", stream, handle_forward_references=True):
                        _save(item, deferred)
                        models.add(type(item.object))
                        loaded += 1
                    # References to rows that came later in the file.
                    for item, company_id in deferred:
                        if company_id:
                            with use_company(company_id):
                                item.save_deferred_fields(using=DEFAULT_DB_ALIAS)
                        else:
                            item.save_deferred_fields(using=DEFAULT_DB_ALIAS)
                connection.check_constraints(table_names=[m._meta.db_table for m in models])
                sql = connection.ops.sequence_reset_sql(no_style(), list(models))
                with connection.cursor() as cursor:
                    for line in sql:
                        cursor.execute(line)
        except FileNotFoundError:
            raise CommandError(f"No such file: {options['file']}") from None
        self.stdout.write(f"Loaded {loaded} rows into {len(models)} tables.")
