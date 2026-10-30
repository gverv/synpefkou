# synet/urls.py

# import debug_toolbar
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import LoginView
from django.urls import include, path

from . import views


def permission_protected(view, *permissions):
    return login_required(
        permission_required(permissions, raise_exception=True)(view)
    )


urlpatterns = [
    # INDEX
    path('', permission_protected(
        views.index,
        'synet.view_watercons',
        'synet.view_paids',
        'synet.view_persons',
    ), name='index'),

    # AUTH
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # CUSTOMERS
    path('customers/', permission_protected(
        views.customers, 'synet.view_persons'
    ), name='customers'),
    path('customers/<int:pk>/update/', login_required(views.PersonsUpdateView.as_view()), name='persons_update'),
    path('customers/<int:customer_id>/irrigations/', login_required(views.CustomerIrrigationsView.as_view()), name='customer_irrigations'),

    # COUNTERS
    path('counters/', permission_protected(
        views.counters, 'synet.view_counters'
    ), name='counters'),
    path('counters/<int:pk>/update/', login_required(views.CountersUpdateView.as_view()), name='counters_update'),
    path('counters/<int:pk>/detail/', permission_protected(
        views.counter_detail,
        'synet.view_counters',
        'synet.view_watercons',
        'synet.view_persons',
    ), name='counter_detail'),

    # PAIDS
    path('paids/', permission_protected(
        views.paids, 'synet.view_paids'
    ), name='paids'),
    path('paids/<int:pk>/update/', login_required(views.PaidsUpdateView.as_view()), name='paids_update'),
    path('paids/add/<int:pk>/', permission_protected(
        views.create_payment,
        'synet.view_watercons',
        'synet.view_persons',
    ), name='create_payment'),

    # CASH TRANSACTIONS
    path('cashtransactions/', login_required(views.CashTransactionListView.as_view()), name='cashtransactions'),
    path('cashtransactions/add/', login_required(views.CashTransactionCreateView.as_view()), name='cashtransaction_add'),
    path('cashtransactions/<int:pk>/update/', login_required(views.CashTransactionUpdateView.as_view()), name='cashtransaction_update'),
    path('cashtransactions/<int:pk>/delete/', login_required(views.CashTransactionDeleteView.as_view()), name='cashtransaction_delete'),

    # IRRIGATIONS / WATERCONSUMPTIONS
    path('irrigations/add/', login_required(views.WaterConsCreateView.as_view()), name='add_irrigation'),
    path('irrigations/<int:pk>/update/', login_required(views.WaterConsUpdateView.as_view()), name='update_irrigation'),

    # AJAX / GET endpoints
    path('ajax/get_person_phone/<int:person_id>/', permission_protected(
        views.get_person_phone, 'synet.view_persons'
    ), name='get_person_phone'),
    path('ajax/get_params_for_watercons/', permission_protected(
        views.get_params_for_watercons,
        'synet.view_watercons',
        'synet.view_persons',
    ), name='get_params_for_watercons'),
    path('ajax/get_counter_last_reading/<int:counter_id>/', permission_protected(
        views.get_counter_last_reading, 'synet.view_watercons'
    ), name='get_counter_last_reading'),
    path('ajax/get_watercons_params/', permission_protected(
        views.get_watercons_params,
        'synet.view_watercons',
        'synet.view_persons',
    ), name='get_watercons_params'),
    path('ajax/get_collector_fee_rate/', permission_protected(
        views.get_collector_fee_rate, 'synet.view_paids'
    ), name='get_collector_fee_rate'),

    # REPORT
    path('report/select-persons/', permission_protected(
        views.select_persons_for_report, 'synet.view_persons'
    ), name='select_persons_for_report'),
    path('report/', permission_protected(
        views.report_view, 'synet.view_persons', 'synet.view_paids'
    ), name='report'),
    path('report/hydronomist/', permission_protected(
        views.hydronomist_report_view,
        'synet.view_watercons',
        'synet.view_persons',
    ), name='hydronomist_report'),
    path('report/collector/', permission_protected(
        views.collector_report_view, 'synet.view_paids'
    ), name='collector_report'),
    path('report/counters/', permission_protected(
        views.counter_list_report_view,
        'synet.view_counters',
        'synet.view_persons',
    ), name='counter_list_report'),
    path('report/counter-readings/', permission_protected(
        views.counter_readings_report_view,
        'synet.view_counters',
        'synet.view_watercons',
        'synet.view_persons',
    ), name='counter_readings_report'),

    # SEARCH
    path('search/', login_required(views.global_search), name='global_search'),
]

# urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
