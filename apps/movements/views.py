from django.views.generic import ListView, DetailView
from django.db.models import Q
from apps.core.mixins import WorkerRequiredMixin
from apps.users.models import User
from .models import Movement


class MovementListView(WorkerRequiredMixin, ListView):
    model = Movement
    template_name = "movements/movement_list.html"
    context_object_name = "movements"
    paginate_by = 50

    def get_queryset(self):
        qs = Movement.objects.select_related(
            "worker", "table_session__client", "product_account__client", "machine"
        ).order_by("-created_at")

        worker = self.request.GET.get("worker")
        source = self.request.GET.get("source")
        search = self.request.GET.get("q", "").strip()

        if worker:
            qs = qs.filter(worker_id=worker)
        if source:
            qs = qs.filter(source=source)
        if search:
            qs = qs.filter(description__icontains=search)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["workers"] = User.objects.filter(is_active=True).order_by("first_name")
        ctx["sources"] = Movement._meta.get_field("source").choices
        ctx["selected_worker"] = self.request.GET.get("worker", "")
        ctx["selected_source"] = self.request.GET.get("source", "")
        ctx["search_q"] = self.request.GET.get("q", "")
        return ctx


class MovementDetailView(WorkerRequiredMixin, DetailView):
    model = Movement
    template_name = "movements/movement_detail.html"
    context_object_name = "movement"
