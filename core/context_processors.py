from .models import SiteSettings

def site_settings(request):
    try:
        settings = SiteSettings.objects.first()
        return {'site_settings': settings}
    except:
        return {'site_settings': None}
