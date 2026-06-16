from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType


class ChangeHistoryMixin:
    """
    Add this mixin to any ModelAdmin to show Django's change history
    in the right sidebar of the change form page.
    """
    change_form_template = 'admin/shared_change_form.html'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        ct = ContentType.objects.get_for_model(self.model)
        extra_context['change_history'] = LogEntry.objects.filter(
            content_type=ct, object_id=object_id
        ).select_related('user').order_by('-action_time')[:50]
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
