# forms.py
import datetime
from datetime import date

from django import forms
from django.contrib.auth.models import User
from django.forms import ModelForm, NumberInput, Select, TextInput

from .models import (CashTransaction, Counters, Fields, Paids, Persons,
                     Receivers, TransactionCategory, TransactionType,
                     WaterCons, Ydronomeas)


class HydronomistReportForm(forms.Form):
    date_from = forms.DateField(
        label="Ημερομηνία από",
        required=False,
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d',
        ),
    )
    date_to = forms.DateField(
        label="Ημερομηνία έως",
        required=False,
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d',
        ),
    )
    ydronomeas = forms.ModelChoiceField(
        label="Υδρονομέας",
        queryset=Ydronomeas.objects.order_by('ydronomeas'),
        required=False,
        empty_label="Όλοι οι υδρονομείς",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        if date_from and date_to and date_from > date_to:
            self.add_error('date_to', "Η ημερομηνία έως πρέπει να είναι ίση ή μεταγενέστερη.")
        return cleaned_data


class CollectorReportForm(forms.Form):
    date_from = forms.DateField(
        label="Ημερομηνία από",
        required=False,
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d',
        ),
    )
    date_to = forms.DateField(
        label="Ημερομηνία έως",
        required=False,
        widget=forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'},
            format='%Y-%m-%d',
        ),
    )
    receiver = forms.ModelChoiceField(
        label="Εισπράκτορας",
        queryset=Receivers.objects.order_by('receiver'),
        required=False,
        empty_label="Όλοι οι εισπράκτορες",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        if date_from and date_to and date_from > date_to:
            self.add_error('date_to', "Η ημερομηνία έως πρέπει να είναι ίση ή μεταγενέστερη.")
        return cleaned_data


class WaterConsForm(ModelForm):
    class Meta:
        model = WaterCons
        fields = [
            'date', 
            'counter', 
            'customer', 
            'finalIndication', 
            'initialIndication', 
            'cubicMeters', 
            'billableCubicMeters', 
            'ydronomistFee',
            'ydronomeas',
            'costPerMeter',
            'cost', 
            'hydronomistsRight', 
            'msg',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }
        labels = {
         'date': 'Ημ/νία',
         'counter': "Μετρητής",
         'customer': "Καταναλωτής",
         'finalIndication': "Τελική",
         'initialIndication': "Αρχική",
         'cubicMeters': "Κυβικά",
         'billableCubicMeters': "Χρεώσιμα",
         'ydronomistFee': "Ανά κυβικό στον Υδρονομέα",
         'ydronomeas': "Υδρονομέας",
         'costPerMeter': 'ΑνάΚυβικό',
         'cost': "Κόστος",
         'hydronomistsRight': "Δικαίωμα Υδρονομέα",
         'msg': "Μήνυμα",
        #  'notes': "Σημειώσεις",
        #  'field': "Χωράφι",
        #  'receipt': "Απόδειξη"
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['counter'].initial = 1
            self.fields['ydronomeas'].initial = 1
            latest_date = WaterCons.objects.order_by('-id').values_list(
                'date', flat=True
            ).first()
            self.fields['date'].initial = (
                latest_date + datetime.timedelta(days=1)
                if latest_date else date.today()
            )
                
class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

        
class PersonsForm(forms.ModelForm):
    class Meta:
        model = Persons
        fields = '__all__'
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'onoma@example.com',
                'autocomplete': 'email',
            }),
        }
        help_texts = {
            'afm': 'Συμπληρώστε 9 ψηφία.',
            'email': 'π.χ. onoma@example.com',
        }
        labels = {
            'surname': 'Επώνυμο',
            'name': 'Όνομα',
            'fathersName': 'Πατρώνυμο',
            'afm': 'ΑΦΜ',
            'phone': 'Τηλέφωνο',
            'member': 'Μέλος',
            'payAsMember': 'Πληρωμή ως μέλος',
            'isActive': 'Ενεργός',
            'aa': 'Α/Α μέλους',
            'placeOfResidence': 'Κατοικία',
            'notes': 'Σημειώσεις',
        }

    def clean_afm(self):
        afm = self.cleaned_data.get('afm')
        if not afm:
            return afm

        if not afm.isascii() or not afm.isdigit() or len(afm) != 9:
            raise forms.ValidationError('Το ΑΦΜ πρέπει να αποτελείται από 9 ψηφία.')

        checksum = sum(
            int(digit) * 2 ** (8 - index)
            for index, digit in enumerate(afm[:8])
        ) % 11 % 10
        if afm == '000000000' or checksum != int(afm[-1]):
            raise forms.ValidationError('Το ΑΦΜ δεν είναι έγκυρο.')

        return afm

class CountersForm(forms.ModelForm):
    class Meta:
        model = Counters
        fields = ['customer', 'collecter', 'counter', 'sort_order']
        widgets = {
            'customer': forms.TextInput(attrs={'readonly': 'readonly'}),
            # ...άλλα widgets...
        }
        labels = {
            'customer': 'Καταναλωτης',
            'collecter': 'Κολεκτέρ',
            'counter': 'Μετρητής',
            'sort_order': 'Σειρά ταξινόμησης',
        }        
 

class PaidsForm(forms.ModelForm):
    class Meta:
        model = Paids
        fields = [
            'receiptNumber',  # Αρ Απόδειξης
            'cost',  # Αξία
            'paid',  # Πλήρωσε
            'balance',  # Ισοζύγιο
            'paymentDate',  # Ημ/νία Πληρωμής
            'receiver',  # Εισπράκτορας
            'collectorFeeRate',  # Ποσοστό Εισπράκτορα
            'collectorFee',  # Αμοιβή Εισπράκτορα
            'notes',
            # 'irrigation',  # Ποτισμός
            # 'customer',  # Καταναλωτής
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
            'paymentDate': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            # 'paymentDate': forms.DateInput(attrs={'type': 'date'}),
            # 'irrigation': forms.TextInput(attrs={'readonly': 'readonly'}),
            # 'customer': forms.TextInput(attrs={'readonly': 'readonly'}),
            'collectorFeeRate': forms.NumberInput(attrs={'step': '0.01'}),
            'collectorFee': forms.NumberInput(attrs={'step': '0.01'}),
        }
        labels = {
            'receiptNumber': 'Αρ Απόδειξης',
            'cost': 'Αξία',
            'paid': 'Πλήρωσε',
            'balance': 'Ισοζύγιο',
            'paymentDate': 'Ημ/νία Πληρωμής',
            'receiver': 'Εισπράκτορας',
            'irrigation': 'Ποτισμός',
            'customer': 'Καταναλωτής',
            'collectorFeeRate': 'Ποσοστό Εισπράκτορα',
            'collectorFee': 'Αμοιβή Εισπράκτορα',
            'notes': 'Σημειώσεις',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Βάλε default τιμές ή readonly ρυθμίσεις αν χρειάζεται
        self.fields['paid'].initial = self.fields['paid'].initial or 0
        self.fields['balance'].initial = self.fields['balance'].initial or 0

        
class CashTransactionForm(forms.ModelForm):
    class Meta:
        model = CashTransaction
        fields = ['category', 'type', 'amount', 'receiver', 'transaction_date', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'transaction_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['category'].queryset = TransactionCategory.objects.filter(is_active=True)
        self.fields['type'].required = False
        self.fields['type'].empty_label = "Αυτόματα"
        
        if not self.instance.pk and not self.data.get('receiver'):
            self.fields['receiver'].initial = 1

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        if category and category.type:
            cleaned_data['type'] = category.type
        return cleaned_data
