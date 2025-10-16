from django.core.management.base import BaseCommand, CommandError
from backup.views import _load_fixture_items_from_path, group_fixture_by_model, get_model_from_label, infer_unique_keys_for_model, now_human
from backup.models import RestoreJob
from django.db.models import Q
import json

class Command(BaseCommand):
    help = 'Validate a backup/export file for restore and print a preview JSON.'

    def add_arguments(self, parser):
        parser.add_argument('--file', dest='file', help='Path to JSON backup/export file')
        parser.add_argument('--mode', dest='mode', default='merge', choices=['merge','replace'])
        parser.add_argument('--strategy', dest='strategy', default='update', choices=['skip','update'])

    def handle(self, *args, **options):
        path = options.get('file')
        if not path:
            raise CommandError('Provide --file path')
        mode = options['mode']
        strategy = options['strategy']
        items = _load_fixture_items_from_path(path)
        grouped = group_fixture_by_model(items)
        per_table = {}
        total = {'inserts': 0, 'updates': 0, 'skips': 0, 'conflicts': 0}
        for label, rows in grouped.items():
            model = get_model_from_label(label)
            if not model:
                continue
            keys = infer_unique_keys_for_model(model)
            inserts = updates = skips = conflicts = 0
            sample_conflicts = []
            for item in rows:
                fields = item.get('fields', {})
                matched = None
                for key_tuple in keys:
                    q = Q()
                    missing = False
                    for k in key_tuple:
                        if k in fields and fields[k] is not None:
                            q &= Q(**{k: fields[k]})
                        else:
                            missing = True
                            break
                    if missing:
                        continue
                    count = model.objects.filter(q).count()
                    if count == 0:
                        matched = None
                    elif count == 1:
                        matched = 1
                    else:
                        conflicts += 1
                        if len(sample_conflicts) < 5:
                            sample_conflicts.append({'keys': key_tuple, 'values': {k: fields.get(k) for k in key_tuple}})
                        matched = 'conflict'
                    break
                if matched == 'conflict':
                    continue
                if matched is None:
                    inserts += 1
                else:
                    if mode == 'merge':
                        if strategy == 'skip':
                            skips += 1
                        else:
                            updates += 1
                    else:
                        updates += 1
            per_table[label] = {
                'unique_keys': keys,
                'inserts': inserts,
                'updates': updates,
                'skips': skips,
                'conflicts': conflicts,
                'sample_conflicts': sample_conflicts,
            }
            for k in total:
                total[k] += per_table[label][k]
        result = {
            'created_at': now_human(),
            'file_path': path,
            'mode': mode,
            'duplicate_strategy': strategy,
            'tables': per_table,
            'total': total,
        }
        RestoreJob.objects.create(status='pending', source_type='uploaded', file_path=path, format='json', mode=mode, duplicate_strategy=strategy, validation_result_json=result)
        self.stdout.write(json.dumps(result, indent=2))
