from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone


@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    from apps.reports.models import UserSession
    ip = (
        request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        or request.META.get('REMOTE_ADDR')
    )
    UserSession.objects.create(
        user=user,
        login_at=timezone.now(),
        ip_address=ip or None,
        session_key=request.session.session_key or '',
    )


@receiver(user_logged_out)
def on_user_logout(sender, request, user, **kwargs):
    from apps.reports.models import UserSession
    if not user:
        return
    # Cerrar la sesion activa mas reciente de este usuario
    session = UserSession.objects.filter(
        user=user,
        logout_at__isnull=True
    ).order_by('-login_at').first()
    if session:
        session.logout_at = timezone.now()
        session.save(update_fields=['logout_at'])
