import datetime

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=40, blank=True, help_text='Bootstrap Icons name, e.g. "heart-pulse"')
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Doctor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile'
    )
    specialization = models.ForeignKey(
        Specialization, on_delete=models.SET_NULL, null=True, related_name='doctors'
    )
    qualification = models.CharField(max_length=200, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=500)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='doctors/', blank=True)
    available_from = models.TimeField(default=datetime.time(9, 0))
    available_to = models.TimeField(default=datetime.time(17, 0))
    slot_minutes = models.PositiveIntegerField(default=30)
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ['user__first_name']

    def __str__(self):
        return f'Dr. {self.user.get_full_name() or self.user.username}'

    def get_absolute_url(self):
        return reverse('doctor_detail', args=[self.pk])

    def time_slots(self):
        """All consultation start times within the doctor's working hours."""
        slots = []
        start = datetime.datetime.combine(datetime.date.today(), self.available_from)
        end = datetime.datetime.combine(datetime.date.today(), self.available_to)
        step = datetime.timedelta(minutes=self.slot_minutes or 30)
        while start + step <= end:
            slots.append(start.time())
            start += step
        return slots

    def free_slots(self, date):
        taken = set(
            self.appointments.filter(date=date)
            .exclude(status__in=[Appointment.Status.CANCELLED, Appointment.Status.REJECTED])
            .values_list('time', flat=True)
        )
        slots = [s for s in self.time_slots() if s not in taken]
        now = timezone.localtime()
        if date == now.date():
            slots = [s for s in slots if s > now.time()]
        return slots


class Patient(models.Model):
    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_profile'
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    address = models.TextField(blank=True)
    medical_history = models.TextField(blank=True, help_text='Allergies, chronic conditions, etc.')

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = datetime.date.today()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        REJECTED = 'rejected', 'Rejected'

    class Mode(models.TextChoices):
        VIDEO = 'video', 'Video consultation'
        CLINIC = 'clinic', 'In-clinic visit'

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField()
    time = models.TimeField()
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.VIDEO)
    symptoms = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    meeting_link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-time']
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'date', 'time'],
                condition=~models.Q(status__in=['cancelled', 'rejected']),
                name='unique_active_slot_per_doctor',
            )
        ]

    def __str__(self):
        return f'{self.patient} with {self.doctor} on {self.date} {self.time:%H:%M}'

    def get_absolute_url(self):
        return reverse('appointment_detail', args=[self.pk])

    @property
    def is_active(self):
        return self.status in (self.Status.PENDING, self.Status.CONFIRMED)

    @property
    def status_color(self):
        return {
            'pending': 'warning',
            'confirmed': 'primary',
            'completed': 'success',
            'cancelled': 'secondary',
            'rejected': 'danger',
        }[self.status]


class Prescription(models.Model):
    appointment = models.OneToOneField(
        Appointment, on_delete=models.CASCADE, related_name='prescription'
    )
    diagnosis = models.TextField()
    medicines = models.TextField(help_text='One medicine per line, e.g. "Paracetamol 500mg - 1-0-1 - 5 days"')
    advice = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Prescription for {self.appointment}'

    def medicine_list(self):
        return [line.strip() for line in self.medicines.splitlines() if line.strip()]


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} — {self.name}'
