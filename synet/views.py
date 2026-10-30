# views.py
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import F, Q, Sum, Window
from django.db.models.functions import RowNumber
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import (CashTransactionForm, CollectorReportForm, CountersForm,
                    HydronomistReportForm, PaidsForm, PersonsForm, WaterConsForm)
from .models import (CashTransaction, Counters, Fields, Paids, Parametroi,
                     Persons, TransactionCategory, TransactionType, WaterCons)
from .utils import send_sms


def get_sort_params(request, default='-id'):
    sort_by = request.GET.get('sort', default)
    order = request.GET.get('order', 'asc')  # ή 'desc' αν θέλεις default φθίνουσα
    if order == 'desc' and not sort_by.startswith('-'):
        sort_by = f'-{sort_by}'
    elif order == 'asc' and sort_by.startswith('-'):
        sort_by = sort_by[1:]
    return sort_by, 'asc' if order == 'desc' else 'desc'


class ViewOrWritePermissionRequiredMixin(PermissionRequiredMixin):
    view_permission_required = None
    related_view_permissions = ()
    raise_exception = True

    def has_permission(self):
        has_write_permission = super().has_permission()
        has_view_permission = (
            self.request.method in ('GET', 'HEAD', 'OPTIONS')
            and self.view_permission_required
            and self.request.user.has_perm(self.view_permission_required)
        )
        return (
            (has_write_permission or has_view_permission)
            and self.request.user.has_perms(self.related_view_permissions)
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not self.request.user.has_perms(self.get_permission_required()):
            for field in form.fields.values():
                field.disabled = True
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_write'] = self.request.user.has_perms(
            self.get_permission_required()
        )
        return context


# ---------------------------
# INDEX
# ---------------------------
def index(request):
    sort_by, order = get_sort_params(request, default='-id')  # default φθίνουσα id
    all_mode = request.GET.get('all') == '1'
    # queryset = WaterCons.objects.all().order_by(sort_by)
    queryset = WaterCons.objects.all().order_by('-id')  # Πάντα φθίνουσα id

    aggregates = WaterCons.objects.aggregate(
        total_cost=Sum('cost'),
        total_hydronomists=Sum('hydronomistsRight'),
        total_cubic=Sum('cubicMeters'),
        total_billable=Sum('billableCubicMeters')
    )
    total_paid = Paids.objects.aggregate(total_paid=Sum('paid'))['total_paid'] or 0
    debt = (aggregates['total_cost'] or 0) - total_paid

    if all_mode:
        page_obj = None
        objects = queryset  # Όλες οι εγγραφές με φθίνουσα id
    else:
        paginator = Paginator(queryset, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        objects = page_obj.object_list

    return render(request, 'index.html', {
        'objects': objects,
        'page_obj': page_obj,
        'order': order,
        'sort_by': sort_by,
        **aggregates,
        'total_paid': total_paid,
        'debt': debt,
    })


# ---------------------------
# CUSTOMERS
# ---------------------------
def customers(request):
    sort_by, order = get_sort_params(request, default='surname')
    data = Persons.objects.filter(isActive=True).order_by(sort_by)
    return render(request, 'customers.html', {'data': data, 'order': order})


class PersonsUpdateView(ViewOrWritePermissionRequiredMixin, UpdateView):
    permission_required = 'synet.change_persons'
    view_permission_required = 'synet.view_persons'
    model = Persons
    form_class = PersonsForm
    template_name = 'persons_update.html'
    success_url = reverse_lazy('customers')


# ---------------------------
# COUNTERS
# ---------------------------
def counters(request):
    sort_by, order = get_sort_params(request, default='sort_order')
    data = Counters.objects.all()
    if request.GET.get('sort'):
        data = data.order_by(sort_by)
    return render(request, 'counters.html', {'data': data, 'order': order})


class CountersUpdateView(ViewOrWritePermissionRequiredMixin, UpdateView):
    permission_required = 'synet.change_counters'
    view_permission_required = 'synet.view_counters'
    related_view_permissions = ('synet.view_persons',)
    model = Counters
    form_class = CountersForm
    template_name = 'counters_update.html'
    success_url = reverse_lazy('counters')


# ---------------------------
# PAIDS
# ---------------------------
def paids(request):
    sort_by = request.GET.get('sort', 'receiptNumber')
    order = request.GET.get('order', 'desc')
    sort_field = f'-{sort_by}' if order == 'desc' else sort_by
    all_param = request.GET.get('all')
    all_data = Paids.objects.all().order_by(sort_field)

    if all_param == '1':
        page_obj = all_data
    else:
        paginator = Paginator(all_data, 14)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

    return render(request, 'paids.html', {
        'page_obj': page_obj,
        'order': order,
        'sort_by': sort_by
    })


# ---------------------------
# CASH TRANSACTIONS
# ---------------------------
class CashTransactionListView(PermissionRequiredMixin, ListView):
    permission_required = 'synet.view_cashtransaction'
    model = CashTransaction
    template_name = 'cashtransactions.html'
    context_object_name = 'transactions'
    paginate_by = 20

    def get_queryset(self):
        sort_by, order = get_sort_params(self.request, default='-transaction_date')
        return CashTransaction.objects.all().order_by(sort_by)


class CashTransactionCreateView(ViewOrWritePermissionRequiredMixin, CreateView):
    permission_required = 'synet.add_cashtransaction'
    view_permission_required = 'synet.view_cashtransaction'
    model = CashTransaction
    form_class = CashTransactionForm
    template_name = 'cashtransaction_form.html'
    success_url = reverse_lazy('cashtransactions')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Build category to type mapping from database (using TransactionType ID, not value)
        category_type_map = {}
        for category in TransactionCategory.objects.select_related('type'):
            if category.type:
                category_type_map[str(category.id)] = str(category.type.id)
        context['category_type_map'] = category_type_map
        return context

    def form_valid(self, form):
        messages.success(self.request, '✅ Καταχωρήθηκε επιτυχώς η κίνηση ταμείου.')
        return super().form_valid(form)


class CashTransactionUpdateView(ViewOrWritePermissionRequiredMixin, UpdateView):
    permission_required = 'synet.change_cashtransaction'
    view_permission_required = 'synet.view_cashtransaction'
    model = CashTransaction
    form_class = CashTransactionForm
    template_name = 'cashtransaction_form.html'
    success_url = reverse_lazy('cashtransactions')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Build category to type mapping from database (using TransactionType ID, not value)
        category_type_map = {}
        for category in TransactionCategory.objects.select_related('type'):
            if category.type:
                category_type_map[str(category.id)] = str(category.type.id)
        context['category_type_map'] = category_type_map
        return context

    def form_valid(self, form):
        messages.success(self.request, '✅ Η κίνηση ταμείου ενημερώθηκε επιτυχώς.')
        return super().form_valid(form)


class CashTransactionDeleteView(ViewOrWritePermissionRequiredMixin, DeleteView):
    permission_required = 'synet.delete_cashtransaction'
    view_permission_required = 'synet.view_cashtransaction'
    model = CashTransaction
    template_name = 'cashtransaction_confirm_delete.html'
    success_url = reverse_lazy('cashtransactions')

    def delete(self, request, *args, **kwargs):
        messages.success(request, '✅ Η κίνηση ταμείου διαγράφηκε επιτυχώς.')
        return super().delete(request, *args, **kwargs)



# ---------------------------
# UPDATE PAYMENT
# ---------------------------
class PaidsUpdateView(ViewOrWritePermissionRequiredMixin, UpdateView):
    permission_required = 'synet.change_paids'
    view_permission_required = 'synet.view_paids'
    related_view_permissions = ('synet.view_persons',)
    model = Paids
    form_class = PaidsForm
    template_name = 'paid_create_update.html'
    success_url = reverse_lazy('paids')

    def form_valid(self, form):
        obj = form.save(commit=False)
        if not obj.irrigation:
            obj.irrigation = self.get_object().irrigation
        if not obj.customer:
            obj.customer = self.get_object().customer
        obj.save()

        messages.success(self.request, f"💾 Η απόδειξη #{obj.receiptNumber} ενημερώθηκε επιτυχώς.")
        return super().form_valid(form)


# ---------------------------
# CREATE PAYMENT
# ---------------------------
@require_http_methods(["GET", "POST"])
def create_payment(request, pk):
    can_write = request.user.has_perm('synet.add_paids')
    if request.method == 'POST' and not can_write:
        raise PermissionDenied
    if request.method in ('GET', 'HEAD') and not (
        can_write or request.user.has_perm('synet.view_paids')
    ):
        raise PermissionDenied

    watercons = get_object_or_404(WaterCons, pk=pk)
    last_paid = Paids.objects.order_by("-receiptNumber").first()
    next_receipt_no = (last_paid.receiptNumber + 1) if last_paid else 1
    notes_msg = (request.GET.get('msg') or watercons.msg or '').strip()

    if request.method == "POST":
        form = PaidsForm(request.POST)
        if form.is_valid():
            paid = form.save(commit=False)
            paid.customer = watercons.customer
            paid.irrigation = watercons
            paid.save()
            messages.success(request, f"✅ Δημιουργήθηκε επιτυχώς η απόδειξη #{paid.receiptNumber}.")
            return redirect("paids")
    else:
        initial_notes = f"Αρ. Απόδειξης {next_receipt_no} {notes_msg}" if notes_msg else ''
        form = PaidsForm(initial={
            "receiptNumber": next_receipt_no,
            "cost": watercons.cost,
            "paid": 0,
            "balance": -watercons.cost if watercons.cost is not None else 0,
            "irrigation": watercons,
            "customer": watercons.customer,
            "notes": initial_notes,
            
        })

    if not can_write:
        for field in form.fields.values():
            field.disabled = True

    return render(
        request,
        "paid_create_update.html",
        {
            "form": form,
            "msg": notes_msg,
            "irrigation": watercons,
            "can_write": can_write,
        },
    )


# ---------------------------
# WATERCONSUMPTIONS / IRRIGATIONS
# ---------------------------
class WaterConsCreateView(ViewOrWritePermissionRequiredMixin, CreateView):
    permission_required = 'synet.add_watercons'
    view_permission_required = 'synet.view_watercons'
    related_view_permissions = ('synet.view_persons',)
    model = WaterCons
    form_class = WaterConsForm
    template_name = 'irrigation_create_update.html'
    success_url = reverse_lazy('index')

    # ---------------------------------------------------
    # Προετοιμασία φόρμας
    # ---------------------------------------------------
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        self._configure_customer_field(form)
        return form

    def _configure_customer_field(self, form):
        """Εμφανίζει μόνο ενεργούς πελάτες στο dropdown."""
        form.fields['customer'].queryset = Persons.objects.filter(isActive=True)

    # ---------------------------------------------------
    # Form Valid
    # ---------------------------------------------------
    def form_valid(self, form):
        instance = form.instance  # πιο καθαρό από το commit=False

        if not self._validate_fields(form, instance):
            return self.form_invalid(form)

        save_and_receipt = self.request.POST.get('save_and_receipt')
        if save_and_receipt:
            if instance.cost is None or instance.cost <= 0:
                form.add_error('cost', 'Το κόστος πρέπει να είναι μεγαλύτερο από 0 για να εκδοθεί απόδειξη.')
                return self.form_invalid(form)
            self.object = form.save(commit=False)
            self.object.save()
            msg = self.object.msg or ''
            query = urlencode({'msg': msg})
            return redirect(f"{reverse('create_payment', kwargs={'pk': self.object.pk})}?{query}")

        response = super().form_valid(form)  # εδώ γίνεται το save()
        # self._send_sms_if_needed(instance)
        return response

    # ---------------------------------------------------
    # Validation
    # ---------------------------------------------------
    def _validate_fields(self, form, instance):
        """Custom validation για θετικές τιμές."""
        valid = True

        if instance.cubicMeters is not None and instance.cubicMeters < 0:
            form.add_error('cubicMeters', 'Τα κυβικά πρέπει να είναι θετικός αριθμός.')
            valid = False

        if instance.costPerMeter is not None and instance.costPerMeter < 0:
            form.add_error('costPerMeter', 'Το κόστος ανά κυβικό πρέπει να είναι θετικός αριθμός.')
            valid = False

        return valid

    # ---------------------------------------------------
    # SMS
    # ---------------------------------------------------
    def _send_sms_if_needed(self, instance):
        """Στέλνει SMS μόνο αν υπάρχουν όλα τα απαραίτητα δεδομένα."""
        if not (instance.customer and instance.msg):
            return

        phone = getattr(instance.customer, 'phone', None)

        if not phone:
            messages.warning(self.request, "Δεν βρέθηκε τηλέφωνο για τον πελάτη, SMS δεν στάλθηκε.")
            return

        try:
            sms_result = send_sms(phone, instance.msg)
            messages.success(self.request, f"SMS στάλθηκε: {sms_result}")
        except Exception as e:
            messages.error(self.request, f"Σφάλμα κατά την αποστολή SMS: {e}")



class WaterConsUpdateView(ViewOrWritePermissionRequiredMixin, UpdateView):
    permission_required = 'synet.change_watercons'
    view_permission_required = 'synet.view_watercons'
    related_view_permissions = ('synet.view_persons',)
    model = WaterCons
    form_class = WaterConsForm
    template_name = 'irrigation_create_update.html'
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        save_and_receipt = self.request.POST.get('save_and_receipt')
        if save_and_receipt:
            self.object = form.save(commit=False)
            if self.object.cost is None or self.object.cost <= 0:
                form.add_error('cost', 'Το κόστος πρέπει να είναι μεγαλύτερο από 0 για να εκδοθεί απόδειξη.')
                return self.form_invalid(form)
            self.object.save()
            existing_paid = self.object.paid_irrigations.order_by('-pk').first()
            if existing_paid:
                return redirect(
                    'paids_update',
                    pk=existing_paid.pk,
                )
            msg = self.object.msg or ''
            query = urlencode({'msg': msg})
            return redirect(f"{reverse('create_payment', kwargs={'pk': self.object.pk})}?{query}")
        return super().form_valid(form)


# ---------------------------
# CUSTOMER IRRIGATIONS (class-based)
# ---------------------------
class CustomerIrrigationsView(PermissionRequiredMixin, ListView):
    permission_required = (
        'synet.view_watercons',
        'synet.view_persons',
        'synet.view_paids',
    )
    model = WaterCons
    template_name = 'customerIrrigations.html'
    context_object_name = 'data'
    paginate_by = 50

    def get_queryset(self):
        customer_id = self.kwargs.get('customer_id')
        return WaterCons.objects.filter(customer_id=customer_id).order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer_id = self.kwargs.get('customer_id')
        customer = get_object_or_404(Persons, id=customer_id)
        customerPaids = Paids.objects.filter(customer=customer_id).order_by('-receiptNumber')
        aggregates = WaterCons.objects.filter(customer_id=customer_id).aggregate(
            total_cost=Sum('cost'),
            total_cubic=Sum('cubicMeters'),
            total_billable=Sum('billableCubicMeters')
        )
        total_paid = Paids.objects.filter(customer=customer_id).aggregate(total_paid=Sum('paid'))['total_paid'] or 0
        debt = (aggregates['total_cost'] or 0) - total_paid
        context.update({
            'customer': customer,
            'customerPaids': customerPaids,
            'order': 'desc',
            'paids_order': 'desc',
            **aggregates,
            'total_paid': total_paid,
            'debt': debt
        })
        return context


# ---------------------------
# AJAX / GET endpoints
# ---------------------------

@require_GET
def get_counter_last_reading(request, counter_id):
    if not counter_id:
        return JsonResponse({"last_reading": ""})
    last_entry = (
        WaterCons.objects.filter(counter_id=counter_id)
        .order_by("-date", "-id")
        .first()
    )
    if last_entry:
        return JsonResponse({"last_reading": last_entry.finalIndication})
    return JsonResponse({"last_reading": ""})


@require_GET
def get_person_phone(request, person_id):
    phone = ""
    if person_id:
        try:
            person = Persons.objects.get(id=person_id)
            phone = person.phone or ""
        except Persons.DoesNotExist:
            pass
    return JsonResponse({'phone': phone})


@require_GET
def get_params_for_watercons(request):
    customer_id = request.GET.get('customer_id')
    counter_id = request.GET.get('counter_id')
    params = {}

    params['ydronomistFee'] = float(get_param('ydronomistFee', 0) or 0)

    payAsMember = False
    if customer_id:
        try:
            person = Persons.objects.get(id=customer_id)
            payAsMember = person.payAsMember
        except Persons.DoesNotExist:
            pass
    params['payAsMember'] = payAsMember

    cost_per_meter = float(get_param('baseCostPerMeter', 0) or 0)
    if not payAsMember:
        cost_per_meter += float(get_param('additionNotMember', 0) or 0)
    if counter_id and str(counter_id) == "4":
        cost_per_meter += float(get_param('additionSecondPump', 0) or 0)
    params['costPerMeter'] = cost_per_meter

    return JsonResponse(params)


@require_GET
def get_collector_fee_rate(request):
    try:
        rate = Parametroi.objects.get(param="collectorFeeRate").value
    except Parametroi.DoesNotExist:
        rate = "0"
    return JsonResponse({"collectorFeeRate": rate})


def get_param(param_name, default=None):
    try:
        return Parametroi.objects.get(param=param_name).value
    except Parametroi.DoesNotExist:
        return default


# ---------------------------
# REPORT
# ---------------------------
def select_persons_for_report(request):
    persons = Persons.objects.filter(isActive=True)
    if request.method == 'POST':
        selected = request.POST.getlist('persons')
        if 'all' in selected:
            selected = [str(p.id) for p in persons]
        return redirect(f"/report/?persons={','.join(selected)}")
    return render(request, 'select_persons.html', {'persons': persons})


def report_view(request):
    person_ids = request.GET.get('persons', '')
    if person_ids:
        ids = [int(i) for i in person_ids.split(',')]
        persons = Persons.objects.filter(id__in=ids)
    else:
        persons = Persons.objects.none()
    report_data = []
    for person in persons:
        payments = Paids.objects.filter(customer=person).exclude(balance=0)
        total_balance = payments.aggregate(total=Sum('balance'))['total'] or 0
        report_data.append({
            'surname': person.surname,
            'name': person.name,
            'fathersName': person.fathersName,
            'payments': payments,
            'total_balance': total_balance
        })
    grand_total_balance = sum(item['total_balance'] for item in report_data)
    return render(request, 'report.html', {
        'report_data': report_data,
        'grand_total_balance': grand_total_balance
    })


def hydronomist_report_view(request):
    form = HydronomistReportForm(request.GET or None)
    report_rows = []
    total_hydronomists = 0

    if request.GET and form.is_valid():
        filters = {'date__lte': form.cleaned_data['date_to'] or timezone.localdate()}
        if form.cleaned_data['date_from']:
            filters['date__gte'] = form.cleaned_data['date_from']
        watercons = WaterCons.objects.filter(
            **filters,
            customer__isnull=False,
        ).select_related('customer', 'ydronomeas').order_by(
            'date', 'customer__surname', 'customer__name'
        )
        if form.cleaned_data['ydronomeas']:
            watercons = watercons.filter(ydronomeas=form.cleaned_data['ydronomeas'])

        report_rows = list(watercons)
        total_hydronomists = watercons.aggregate(
            total=Sum('hydronomistsRight')
        )['total'] or 0

    return render(request, 'hydronomist_report.html', {
        'form': form,
        'report_rows': report_rows,
        'total_hydronomists': total_hydronomists,
    })


def collector_report_view(request):
    form = CollectorReportForm(request.GET or None)
    report_rows = []
    total_collector_fee = 0

    if request.GET and form.is_valid():
        filters = {
            'paymentDate__lte': form.cleaned_data['date_to'] or timezone.localdate(),
        }
        if form.cleaned_data['date_from']:
            filters['paymentDate__gte'] = form.cleaned_data['date_from']

        payments = Paids.objects.filter(
            collectorFee__isnull=False,
            **filters,
        ).exclude(collectorFee=0).select_related('receiver').order_by(
            'paymentDate', 'receiptNumber'
        )
        if form.cleaned_data['receiver']:
            payments = payments.filter(receiver=form.cleaned_data['receiver'])

        report_rows = list(payments)
        total_collector_fee = payments.aggregate(
            total=Sum('collectorFee')
        )['total'] or 0

    return render(request, 'collector_report.html', {
        'form': form,
        'report_rows': report_rows,
        'total_collector_fee': total_collector_fee,
    })


def counter_list_report_view(request):
    counters = Counters.objects.select_related('customer').exclude(
        customer__surname='Συνεταιρισμός',
    ).order_by('collecter', 'counter', 'pk')
    report_rows = [
        ' '.join(value for value in (
            counter.collecter,
            counter.counter,
            ' '.join(
                value for value in (
                    counter.customer.surname,
                    counter.customer.name,
                    counter.customer.fathersName,
                ) if value
            ) if counter.customer else '',
        ) if value)
        for counter in counters
    ]
    return render(request, 'counter_list_report.html', {
        'report_rows': report_rows,
    })


def counter_readings_report_view(request):
    counters = list(
        Counters.objects.select_related('customer').exclude(
            customer__surname='Συνεταιρισμός',
        ).order_by(
            'collecter', 'counter', 'pk'
        )
    )
    readings_by_counter = {counter.pk: [] for counter in counters}
    if readings_by_counter:
        readings = WaterCons.objects.filter(
            counter_id__in=readings_by_counter,
        ).annotate(
            reading_rank=Window(
                expression=RowNumber(),
                partition_by=[F('counter_id')],
                order_by=[F('date').desc(), F('pk').desc()],
            )
        ).filter(
            reading_rank__lte=2,
        ).order_by(
            'counter_id', 'date', 'pk'
        )
    else:
        readings = WaterCons.objects.none()
    for reading in readings:
        readings_by_counter[reading.counter_id].append(reading)

    report_groups = []
    for counter in counters:
        if not report_groups or report_groups[-1]['collecter'] != counter.collecter:
            report_groups.append({'collecter': counter.collecter, 'rows': []})
        report_groups[-1]['rows'].append({
            'counter': counter,
            'readings': readings_by_counter[counter.pk],
        })

    return render(request, 'counter_readings_report.html', {
        'report_groups': report_groups,
    })


def counter_detail(request, pk):
    counter = get_object_or_404(Counters, pk=pk)
    consumptions = WaterCons.objects.filter(counter=counter).order_by('-date', '-finalIndication')
    return render(request, 'counter_detail.html', {
        'counter': counter,
        'consumptions': consumptions
    })
    
    
    
def global_search(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        search_targets = (
            (
                Persons,
                ['surname', 'name', 'fathersName', 'afm', 'phone', 'notes'],
                'Πελάτες',
                'synet.view_persons',
            ),
            (Counters, ['collecter', 'counter'], 'Μετρητές', 'synet.view_counters'),
            (WaterCons, ['msg', 'notes'], 'Ποτίσματα', 'synet.view_watercons'),
            (Paids, ['receiptNumber'], 'Αποδείξεις', 'synet.view_paids'),
            (Fields, ['field'], 'Χωράφια', 'synet.view_fields'),
        )
        for model, fields, model_name, permission in search_targets:
            if request.user.has_perm(permission):
                results += search_model(model, fields, query, model_name)
    return render(request, 'search_results.html', {'results': results, 'query': query})

def search_model(model, fields, query, model_name):
    q = Q()
    for field in fields:
        q |= Q(**{f"{field}__icontains": query})
    found = []
    for obj in model.objects.filter(q):
        for field in fields:
            value = getattr(obj, field, '')
            if query.lower() in str(value).lower():
                url = None
                try:
                    from django.urls import reverse
                    url = reverse(f"{obj._meta.model_name}_detail", args=[obj.id])
                except:
                    pass
                found.append({
                    'model': model_name,
                    'field': field,
                    'value': value,
                    'id': obj.id,
                    'string': str(obj),
                    'url': url,
                })
    return found




def get_watercons_params(request):
    customer_id = request.GET.get('customer_id')
    counter_id = request.GET.get('counter_id')

    def get_param(name, default=0):
        try:
            return float(Parametroi.objects.get(param=name).value)
        except Parametroi.DoesNotExist:
            return default

    ydronomistFee = get_param('ydronomistFee')
    baseCostPerMeter = get_param('baseCostPerMeter')
    additionNotMember = get_param('additionNotMember')
    additionSecondPump = get_param('additionSecondPump')

    # Έλεγχος αν ο πελάτης πληρώνει ως μέλος
    pay_as_member = True
    if customer_id:
        try:
            person = Persons.objects.get(id=customer_id)
            pay_as_member = person.payAsMember
        except Persons.DoesNotExist:
            pay_as_member = True

    is_second_pump = str(counter_id) == "4" if counter_id else False

    costPerMeter = baseCostPerMeter
    if not pay_as_member:
        costPerMeter += additionNotMember
    if is_second_pump:
        costPerMeter += additionSecondPump

    return JsonResponse({
        'ydronomistFee': ydronomistFee,
        'costPerMeter': costPerMeter,
        'payAsMember': pay_as_member,
    })


# ---------------------------
# MY LIST VIEW
# ---------------------------
def my_list_view(request):
    all_mode = request.GET.get('all') == '1'
    queryset = WaterCons.objects.all().order_by('...')

    if all_mode:
        page_obj = None
        objects = queryset  # Όλες οι εγγραφές
    else:
        paginator = Paginator(queryset, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        objects = page_obj.object_list

    return render(request, 'my_template.html', {
        'objects': objects,
        'page_obj': page_obj,
        # ...άλλα context...
    })
