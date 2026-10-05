import datetime
import os

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from clinic.models import Appointment, Doctor, Patient, Prescription, Specialization

DEMO_PASSWORD = 'demo12345'

SPECIALIZATIONS = [
    ('General Physician', 'thermometer-half', 'Fever, cold, infections and everyday health concerns.'),
    ('Cardiology', 'heart-pulse', 'Heart and blood-pressure related conditions.'),
    ('Dermatology', 'droplet-half', 'Skin, hair and nail problems.'),
    ('Pediatrics', 'balloon', 'Healthcare for infants, children and teens.'),
    ('Orthopedics', 'person-walking', 'Bones, joints, muscles and sports injuries.'),
    ('Psychiatry', 'chat-heart', 'Mental health, stress, anxiety and sleep.'),
]

DOCTORS = [
    ('dr_khatri', 'tubelightt', 'khatri', 'General Physician', 'MBBS, MD (Internal Medicine)', 12, 400,
     'Dr. khatri has over a decade of experience treating acute and chronic conditions, with a focus on preventive care.'),
    ('dr_Karki', 'sampu', 'karki', 'Cardiology', 'MBBS, MD, DM (Cardiology)', 15, 900,
     'Interventional cardiologist specialising in hypertension, heart failure and cardiac rehabilitation.'),
    ('dr_Kumari', 'Pirtha', 'kumari', 'Dermatology', 'MBBS, MD (Dermatology)', 8, 600,
     'Treats acne, eczema, psoriasis and hair loss, and offers cosmetic dermatology consultations.'),
    ('dr_Bhattarai', 'Chunnah', 'bhattarai', 'Pediatrics', 'MBBS, DCH, MD (Pediatrics)', 10, 500,
     'Friendly paediatrician covering growth, nutrition, vaccinations and common childhood illnesses.'),
    ('dr_Gaihre', 'Krishna', 'Reddy', 'Orthopedics', 'MBBS, MS (Orthopaedics)', 9, 700,
     'Sports-injury and joint-pain specialist with a focus on non-surgical rehabilitation.'),
    ('dr_Sapkota', 'Sarojni', 'Sapkota', 'Psychiatry', 'MBBS, MD (Psychiatry)', 7, 800,
     'Helps patients with anxiety, depression, sleep issues and stress management.'),
]


class Command(BaseCommand):
    help = f'Load demo specialities, doctors and a patient. All demo accounts use password "{DEMO_PASSWORD}".'

    @transaction.atomic
    def handle(self, *args, **options):
        specs = {}
        for name, icon, desc in SPECIALIZATIONS:
            specs[name], _ = Specialization.objects.update_or_create(
                name=name, defaults={'icon': icon, 'description': desc}
            )

        doctors = []
        for username, first, last, spec, qual, exp, fee, bio in DOCTORS:
            user = self._user(username, first, last, User.Role.DOCTOR)
            doctor, _ = Doctor.objects.update_or_create(
                user=user,
                defaults=dict(
                    specialization=specs[spec], qualification=qual, experience_years=exp,
                    consultation_fee=fee, bio=bio,
                ),
            )
            doctors.append(doctor)

        patient_user = self._user('patient', 'Rahul', 'Verma', User.Role.PATIENT)
        patient, _ = Patient.objects.get_or_create(
            user=patient_user,
            defaults=dict(
                date_of_birth=datetime.date(1995, 6, 15), gender='M', blood_group='B+',
                medical_history='Mild seasonal allergies.',
            ),
        )

        if not patient.appointments.exists():
            today = timezone.localdate()
            past = Appointment.objects.create(
                patient=patient, doctor=doctors[0], date=today - datetime.timedelta(days=7),
                time=datetime.time(10, 0), symptoms='Fever and sore throat for 3 days.',
                status=Appointment.Status.COMPLETED,
            )
            Prescription.objects.create(
                appointment=past,
                diagnosis='Acute viral pharyngitis',
                medicines='Paracetamol 650mg — 1-0-1 — 5 days\nCetirizine 10mg — 0-0-1 — 5 days\nWarm saline gargles — 3 times a day',
                advice='Plenty of fluids and rest. Return if fever persists beyond 5 days.',
            )
            Appointment.objects.create(
                patient=patient, doctor=doctors[2], date=today + datetime.timedelta(days=2),
                time=datetime.time(11, 30), symptoms='Recurring rash on forearms.',
                status=Appointment.Status.CONFIRMED,
                meeting_link='https://meet.jit.si/eclinic-demo-consult',
            )
            Appointment.objects.create(
                patient=patient, doctor=doctors[0], date=today + datetime.timedelta(days=3),
                time=datetime.time(15, 0), symptoms='Follow-up on throat infection.',
            )

        # Site admin for /admin/. Only created when ADMIN_PASSWORD is set, so the
        # password never lives in the code.
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if admin_password:
            admin, _ = User.objects.get_or_create(
                username='admin', defaults={'email': 'admin@eclinic.local', 'first_name': 'Admin'}
            )
            admin.is_staff = admin.is_superuser = True
            admin.set_password(admin_password)
            admin.save()

        self.stdout.write(self.style.SUCCESS(
            f'Demo data ready. Log in as "patient" or "dr_sharma" (password: {DEMO_PASSWORD}).'
        ))

    def _user(self, username, first, last, role):
        user, created = User.objects.get_or_create(
            username=username,
            defaults=dict(first_name=first, last_name=last, role=role, email=f'{username}@eclinic.local'),
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        return user
