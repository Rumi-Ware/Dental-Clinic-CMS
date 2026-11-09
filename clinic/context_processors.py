def deployment_flags(request):
    """Expose safe presentation flags; never expose secrets or paths."""
    from django.conf import settings
    return {"RUMI_DEMO_MODE": settings.RUMI_DEMO_MODE}
