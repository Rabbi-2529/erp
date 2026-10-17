"""The whole database as one JSON file - every company, every table.

    python manage.py export_json full-db.json
    python manage.py loaddata full-db.json          (on another, freshly migrated database)

Django's own ``dumpdata`` cannot read this project: company tables refuse a
query without a company (``TenantManager``), and a many-to-many field to a
company table (a membership's allowed branches) is always read through that
manager. This does what ``dumpdata --natural-foreign`` does, reading each
company's rows inside that company's context. It only reads.

Left out, as ``dumpdata`` usually is: content types and permissions (the
target database makes its own; references to them travel by natural key),
sessions and the admin log.

The file holds everything - password hashes, pay, personal details. Keep it
private and never commit it. Encrypted values (mail passwords, API keys)
open only where the server's SECRET_KEY is the same.
"""

from django.apps import apps
from django.core import serializers
from django.core.management.base import BaseCommand
from django.db import router

from common.models import TenantOwned
from common.tenant import use_company
from tenants.models import Company

SKIP = {"contenttypes.contenttype", "auth.permission", "sessions.session", "admin.logentry"}


def _models():
    """Every model to export, ordered so a row comes after what it refers to."""
    app_list = {}
    for config in apps.get_app_configs():
        chosen = [m for m in config.get_models() if m._meta.label_lower not in SKIP
                  and not m._meta.proxy and m._meta.managed and router.allow_migrate_model("default", m)]
        if chosen:
            app_list[config] = chosen
    return serializers.sort_dependencies(app_list.items(), allow_cycles=True)


def _rows(models, companies, counts):
    for model in models:
        base = model._base_manager.order_by("pk")
        label = model._meta.label
        if issubclass(model, TenantOwned):
            for company_id in companies:
                # Each company's rows inside its own context, so many-to-many
                # fields to company tables can be read.
                with use_company(company_id):
                    for row in base.filter(company_id=company_id).iterator(chunk_size=2000):
                        counts[label] = counts.get(label, 0) + 1
                        yield row
        else:
            for row in base.iterator(chunk_size=2000):
                counts[label] = counts.get(label, 0) + 1
                yield row


class Command(BaseCommand):
    help = "Write the whole database (every company) to one JSON file, loadable with loaddata."

    def add_arguments(self, parser):
        parser.add_argument("output", help="The file to write, e.g. full-db.json")
        parser.add_argument("--indent", type=int, default=None, help="Pretty-print with this indent.")

    def handle(self, *args, **options):
        companies = list(Company.objects.order_by("pk").values_list("pk", flat=True))
        counts = {}
        with open(options["output"], "w", encoding="utf-8") as stream:
            serializers.serialize("json", _rows(_models(), companies, counts), stream=stream,
                                  indent=options["indent"], use_natural_foreign_keys=True,
                                  use_natural_primary_keys=False)
        self.stdout.write(f"Wrote {sum(counts.values())} rows from {len(counts)} tables to {options['output']}.")
