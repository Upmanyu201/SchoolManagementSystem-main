from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from backup.views import _load_fixture_items_from_path, group_fixture_by_model, get_model_from_label, _apply_replace, _apply_merge, now_human
from backup.models import RestoreJob

class Command(BaseCommand):
    help = 'Apply a restore from a backup/export file with mode and duplicate strategy.'

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

        model_order = [
            'core.academicclass','core.section','school_profile.schoolprofile','teachers.teacher','subjects.subject','students.student','fees.feestype','transport.route','transport.stoppage','transport.transportassignment','student_fees.feedeposit','fines.fine','attendance.attendance'
        ]

        job = RestoreJob.objects.create(status='running', source_type='uploaded', file_path=path, format='json', mode=mode, duplicate_strategy=strategy)
        report = {}
        with transaction.atomic():
            if mode == 'replace':
                _apply_replace(grouped, model_order, report)
            else:
                for label in model_order + [l for l in grouped.keys() if l not in model_order]:
                    rows = grouped.get(label)
                    if not rows:
                        continue
                    model = get_model_from_label(label)
                    if not model:
                        continue
                    acc = report.setdefault(label, {'inserted': 0, 'updated': 0, 'skipped': 0, 'conflicts': 0, 'errors': 0})
                    _apply_merge(model, rows, strategy, acc)
        totals = {'inserted': 0, 'updated': 0, 'skipped': 0, 'conflicts': 0, 'errors': 0}
        for r in report.values():
            for k in totals:
                totals[k] += r.get(k, 0)
        job.status = 'success'
        job.report_json = {
            'created_at': now_human(),
            'mode': mode,
            'duplicate_strategy': strategy,
            'per_table': report,
            'total': totals,
        }
        job.save(update_fields=['status', 'report_json'])
        self.stdout.write(self.style.SUCCESS(f"Restore applied (job id {job.id})"))
