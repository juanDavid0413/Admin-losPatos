from django.urls import path
from . import views

app_name = "stock_entries"

urlpatterns = [
    path("", views.StockEntryListView.as_view(), name="list"),
    path("nueva/", views.StockEntryCreateView.as_view(), name="create"),
]
