"""Unit, integration and system tests for E-Clinic.

The flow tests in tests.py cover the main user journeys; this file adds:
- UnitTests: model methods and form validation in isolation
- IntegrationTests: requests through URLs, views, forms and the database
- SystemTestCases: test cases TC01-TC10 from the user's point of view
"""
import datetime

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.forms import DoctorProfileForm
from accounts.models import User

from .forms import AppointmentForm
from .models import Appointment, ContactMessage, Doctor, Patient, Prescription, Specialization

PW = 'pw12345!x'


class Base(TestCase):
    """One specialization, one doctor and one patient, plus a helper to create appointments."""

    def setUp(self):
        self.spec = Specialization.objects.create(name='General Physician')
        du = User.objects.create_user('doc', password=PW, role=User.Role.DOCTOR, first_name='Ana', last_name='Rai')
        self.doctor = Doctor.objects.create(user=du, specialization=self.spec, qualification='MBBS')
        pu = User.objects.create_user('pat', password=PW, role=User.Role.PATIENT)
        self.patient = Patient.objects.create(user=pu)
        self.tomorrow = timezone.localdate() + datetime.timedelta(days=1)

    def appt(self, time=datetime.time(10, 0), status='pending', mode='video'):
        return Appointment.objects.create(patient=self.patient, doctor=self.doctor, date=self.tomorrow,
                                          time=time, mode=mode, symptoms='x', status=status)


class UnitTests(Base):
    def test_u01_time_slots_count(self):
        self.assertEqual(len(self.doctor.time_slots()), 16)  # 09:00-17:00, 30 min

    def test_u02_custom_slot_length(self):
        self.doctor.slot_minutes = 60
        self.assertEqual(len(self.doctor.time_slots()), 8)

    def test_u03_free_slots_excludes_booked(self):
        self.appt()
        self.assertNotIn(datetime.time(10, 0), self.doctor.free_slots(self.tomorrow))

    def test_u04_free_slots_includes_cancelled(self):
        self.appt(status='cancelled')
        self.assertIn(datetime.time(10, 0), self.doctor.free_slots(self.tomorrow))

    def test_u05_free_slots_excludes_past_today(self):
        now = timezone.localtime()
        self.assertTrue(all(s > now.time() for s in self.doctor.free_slots(now.date())))

    def test_u06_patient_age(self):
        today = datetime.date.today()
        self.patient.date_of_birth = today.replace(year=today.year - 20)
        self.assertEqual(self.patient.age, 20)

    def test_u07_age_none_without_dob(self):
        self.assertIsNone(self.patient.age)

    def test_u08_medicine_list(self):
        rx = Prescription(medicines='A 500mg\n\n  B 10mg  \n')
        self.assertEqual(rx.medicine_list(), ['A 500mg', 'B 10mg'])

    def test_u09_form_rejects_past_date(self):
        past = timezone.localdate() - datetime.timedelta(days=1)
        f = AppointmentForm({'date': past, 'time': '10:00', 'mode': 'video', 'symptoms': 'x'},
                            doctor=self.doctor, date=self.tomorrow)
        self.assertFalse(f.is_valid())
        self.assertIn('date', f.errors)

    def test_u10_form_rejects_beyond_60_days(self):
        far = timezone.localdate() + datetime.timedelta(days=61)
        f = AppointmentForm({'date': far, 'time': '10:00', 'mode': 'video', 'symptoms': 'x'},
                            doctor=self.doctor, date=far)
        self.assertFalse(f.is_valid())

    def test_u11_profile_form_rejects_bad_hours(self):
        f = DoctorProfileForm({'specialization': self.spec.pk, 'experience_years': 1, 'consultation_fee': 500,
                               'available_from': '17:00', 'available_to': '09:00', 'slot_minutes': 30},
                              instance=self.doctor)
        self.assertFalse(f.is_valid())

    def test_u12_db_constraint_blocks_double_booking(self):
        self.appt()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.appt()

    def test_u13_role_properties(self):
        self.assertTrue(self.doctor.user.is_doctor)
        self.assertTrue(self.patient.user.is_patient)

    def test_u14_status_color(self):
        self.assertEqual(self.appt().status_color, 'warning')


class IntegrationTests(Base):
    def test_i01_confirm_video_creates_meeting_link(self):
        a = self.appt()
        self.client.login(username='doc', password=PW)
        self.client.post(reverse('appointment_action', args=[a.pk, 'confirm']))
        a.refresh_from_db()
        self.assertTrue(a.meeting_link.startswith('https://meet.jit.si/eclinic-'))

    def test_i02_confirm_clinic_has_no_link(self):
        a = self.appt(mode='clinic')
        self.client.login(username='doc', password=PW)
        self.client.post(reverse('appointment_action', args=[a.pk, 'confirm']))
        a.refresh_from_db()
        self.assertEqual((a.status, a.meeting_link), ('confirmed', ''))

    def test_i03_no_prescription_on_pending(self):
        a = self.appt()
        self.client.login(username='doc', password=PW)
        self.client.post(reverse('write_prescription', args=[a.pk]), {'diagnosis': 'x', 'medicines': 'y'})
        self.assertFalse(Prescription.objects.exists())

    def test_i04_open_redirect_blocked(self):
        a = self.appt()
        self.client.login(username='doc', password=PW)
        r = self.client.post(reverse('appointment_action', args=[a.pk, 'confirm']), {'next': 'https://evil.com/'})
        self.assertEqual(r.url, a.get_absolute_url())

    def test_i05_doctor_search(self):
        r = self.client.get(reverse('doctor_list'), {'q': 'Ana'})
        self.assertContains(r, 'Rai')
        r = self.client.get(reverse('doctor_list'), {'q': 'zzz'})
        self.assertEqual(len(r.context['doctors']), 0)

    def test_i06_contact_form_saves(self):
        self.client.post(reverse('contact'), {'name': 'A', 'email': 'a@b.com', 'subject': 's', 'message': 'm'})
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_i07_doctor_signup_creates_profile(self):
        self.client.post(reverse('signup_doctor'), {
            'username': 'newdoc', 'first_name': 'N', 'last_name': 'D', 'email': 'n@d.com',
            'password1': 'Strong-pass-123', 'password2': 'Strong-pass-123',
            'specialization': self.spec.pk, 'qualification': 'MBBS', 'experience_years': 2,
            'consultation_fee': 500})
        self.assertTrue(Doctor.objects.filter(user__username='newdoc').exists())

    def test_i08_dashboard_counts(self):
        self.appt()
        self.client.login(username='pat', password=PW)
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.context['counts']['pending'], 1)


class SystemTestCases(Base):
    """End-to-end test cases TC01-TC10."""

    def test_tc01_valid_login(self):
        r = self.client.post(reverse('login'), {'username': 'pat', 'password': PW})
        self.assertRedirects(r, reverse('dashboard'))

    def test_tc02_invalid_login(self):
        r = self.client.post(reverse('login'), {'username': 'pat', 'password': 'wrong'})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context['form'].non_field_errors())

    def test_tc03_empty_required_field(self):
        r = self.client.post(reverse('signup'), {'username': '', 'password1': '', 'password2': ''})
        self.assertIn('username', r.context['form'].errors)

    def test_tc04_book_free_slot(self):
        self.client.login(username='pat', password=PW)
        self.client.post(reverse('book_appointment', args=[self.doctor.pk]),
                         {'date': self.tomorrow.isoformat(), 'time': '10:00', 'mode': 'video', 'symptoms': 'x'})
        self.assertEqual(Appointment.objects.get().status, 'pending')

    def test_tc05_book_taken_slot(self):
        self.appt()
        self.client.login(username='pat', password=PW)
        r = self.client.post(reverse('book_appointment', args=[self.doctor.pk]),
                             {'date': self.tomorrow.isoformat(), 'time': '10:00', 'mode': 'video', 'symptoms': 'x'})
        self.assertIn('time', r.context['form'].errors)

    def test_tc06_patient_cannot_confirm(self):
        a = self.appt()
        self.client.login(username='pat', password=PW)
        r = self.client.post(reverse('appointment_action', args=[a.pk, 'confirm']))
        self.assertEqual(r.status_code, 403)

    def test_tc07_doctor_confirms_video(self):
        a = self.appt()
        self.client.login(username='doc', password=PW)
        self.client.post(reverse('appointment_action', args=[a.pk, 'confirm']))
        a.refresh_from_db()
        self.assertEqual(a.status, 'confirmed')
        self.assertTrue(a.meeting_link)

    def test_tc08_prescription_completes(self):
        a = self.appt(status='confirmed')
        self.client.login(username='doc', password=PW)
        self.client.post(reverse('write_prescription', args=[a.pk]),
                         {'diagnosis': 'Flu', 'medicines': 'Paracetamol 500mg'})
        a.refresh_from_db()
        self.assertEqual(a.status, 'completed')

    def test_tc09_cancel_frees_slot(self):
        a = self.appt()
        self.client.login(username='pat', password=PW)
        self.client.post(reverse('appointment_action', args=[a.pk, 'cancel']))
        self.assertIn(datetime.time(10, 0), self.doctor.free_slots(self.tomorrow))

    def test_tc10_anonymous_dashboard_redirects(self):
        r = self.client.get(reverse('dashboard'))
        self.assertTrue(r.url.startswith(reverse('login')))
