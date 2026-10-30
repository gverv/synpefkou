from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F
from django.utils import timezone


class Persons(models.Model):
    surname = models.CharField(max_length=100)
    name = models.CharField(max_length=100, null=True, blank=True)
    fathersName = models.CharField(max_length=100, null=True, blank=True)
    afm = models.CharField(max_length=9, null=True, blank=True, unique=True)
    member = models.BooleanField(default=True)  # Είναι μέλος του συνεταιρισμού
    payAsMember = models.BooleanField(default=True)  # Πληρώνει σαν μέλος του συνεταιρισμού
    isActive = models.BooleanField(default=False)  # Είναι ενεργός στον ποτισμό
    aa = models.IntegerField(null=True, blank=True, unique=True)  # Αύξων αριθμός απόφασης ΔΣ 7/10/2000
    phone = models.CharField(max_length=30, null=True, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    placeOfResidence = models.CharField(max_length=20, null=True, blank=True) # Τόπος διαμονής
    notes = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        unique_together = ('surname', 'name', 'fathersName')
        ordering = ['surname', 'name', 'fathersName']
    
    def __str__(self):
        return f"{self.surname} {self.name} {self.fathersName}".strip()

    @classmethod
    def customers(cls):
        return cls.objects.filter(isActive=True)

    @classmethod
    def members(cls):
        return cls.objects.filter(member=True)    


class Counters(models.Model):
    collecter = models.CharField(max_length=20)
    counter = models.CharField(max_length=20, null=True, blank=True)
    customer = models.ForeignKey(Persons, null=True, blank=True, on_delete=models.SET_NULL)
    sort_order = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = [F('sort_order').asc(nulls_last=True), 'collecter']
        
    def __str__(self):
        return f"{self.collecter} {self.counter} {self.customer}".strip()

class Receivers(models.Model):
    receiver = models.CharField(max_length=30)
    
    def __str__(self):
        return self.receiver
    

class Fields(models.Model):
    customer = models.ForeignKey(Persons, on_delete=models.SET_NULL, null=True)
    field = models.CharField(max_length=20, null=True, blank=True)
    olivesNumber = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.customer} {self.field}".strip()  # Αφαιρεί επιπλέον κενά


        
class Ydronomeas(models.Model):
    ydronomeas = models.CharField(max_length=30)
    
    def __str__(self):
        return self.ydronomeas


class WaterCons(models.Model):
    date = models.DateField()
    counter = models.ForeignKey(Counters, on_delete=models.SET_NULL, null=True)
    customer = models.ForeignKey(Persons, on_delete=models.SET_NULL, null=True)
    finalIndication = models.IntegerField()
    initialIndication = models.IntegerField()
    intermediateIndication = models.IntegerField(null=True, blank=True)
    cubicMeters = models.IntegerField(null=True, blank=True)
    billableCubicMeters = models.IntegerField(null=True, blank=True)
    ydronomistFee = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True) #, default=0.05)  # Ποσοστό υδρονομέα
    costPerMeter = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) #, default=0.30)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hydronomistsRight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ydronomeas = models.ForeignKey(Ydronomeas, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Υδρονομέας")
    msg = models.CharField(max_length=200, null=True, blank=True)
    notes = models.TextField( null=True,blank=True)
    field = models.ForeignKey(Fields, on_delete=models.SET_NULL, null=True, blank=True)
    receipt = models.ForeignKey("Paids", on_delete=models.SET_NULL, null=True, blank=True, related_name="watercons_receipts") # idΑπόδειξης (paids_id)
        
    def __str__(self):
        return f"{self.customer} {self.date} {self.billableCubicMeters} {self.cost}".strip()


class Paids(models.Model):
    irrigation = models.ForeignKey(WaterCons, on_delete=models.SET_NULL, null=True, blank=True, related_name="paid_irrigations")
    customer = models.ForeignKey(Persons, on_delete=models.SET_NULL, null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    receiptNumber = models.IntegerField(null=True, blank=True, unique=True)
    paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    paymentDate = models.DateField(null=True, blank=True)
    receiver = models.ForeignKey(Receivers, on_delete=models.SET_NULL, null=True, blank=True,   verbose_name="Ταμίας")
    collectorFeeRate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) #, default=0.06)  # Ποσοστό εισπράκτορα
    collectorFee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.receiptNumber} {self.irrigation} {self.paymentDate} {self.paid}".strip()

class Parametroi(models.Model):
    param = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, blank=True)
    value = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.param}: {self.value}"


class TransactionType(models.Model):
    name = models.CharField(max_length=50, verbose_name="Όνομα Τύπου")
    value = models.SmallIntegerField(verbose_name="Τιμή", unique=True)
    notes = models.CharField(max_length=200, blank=True, verbose_name="Σημειώσεις")

    def __str__(self):
        return f"{self.name} ({self.value})"

    class Meta:
        verbose_name = "Τύπος Συναλλαγής"
        verbose_name_plural = "Τύποι Συναλλαγών"
        ordering = ['value']


class TransactionCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="Όνομα Κατηγορίας")
    type = models.ForeignKey(TransactionType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Τύπος")
    notes = models.CharField(max_length=200, blank=True, verbose_name="Σημειώσεις")
    is_active = models.BooleanField(default=True, verbose_name="Ενεργή")

    def __str__(self):
        return f"{self.name} ({self.type.name if self.type else 'Χωρίς τύπο'})"

    class Meta:
        verbose_name = "Κατηγορία Συναλλαγής"
        verbose_name_plural = "Κατηγορίες Συναλλαγών"
        ordering = ['name']


class CashTransaction(models.Model):
    category = models.ForeignKey(TransactionCategory, on_delete=models.PROTECT, verbose_name="Κατηγορία")
    type = models.ForeignKey(TransactionType, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Τύπος")
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Ποσό",
        validators=[MinValueValidator(0.01)],
    )
    receiver = models.ForeignKey(Receivers, on_delete=models.SET_NULL, null=True, blank=True,  verbose_name="Ταμίας")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ημερομηνία καταχώρησης")
    transaction_date = models.DateField(default=timezone.localdate, verbose_name="Ημερομηνία συναλλαγής")
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Σημειώσεις"
    )

    def save(self, *args, **kwargs):
        if self.category and self.category.type:
            self.type = self.category.type
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.transaction_date:%d/%m/%Y} - "
            f"{self.category.name if self.category else 'N/A'} - "
            f"{self.amount:.2f} €"
        )

    class Meta:
        verbose_name = "Κίνηση Ταμία"
        verbose_name_plural = "Κινήσεις Ταμία"
        ordering = ["-transaction_date"]
