# E-Clinic - Online Clinic Management System

E-Clinic is a web application for running a small clinic online. Patients find doctors, book video or in-clinic
appointments and receive digital prescriptions. Doctors manage their appointment requests, hold video
consultations and write prescriptions from their own dashboard. Clinic staff manage every record from the
Django admin panel.

## Features

- **Two kinds of accounts** - patients and doctors sign up through separate forms and each get their own dashboard.
- **Doctor directory** - search doctors by name, speciality or qualification and filter by speciality.
- **Slot booking** - time slots are generated from each doctor's working hours and slot length. Booked and past
  slots are hidden, and a database constraint stops two patients from booking the same slot.
- **Appointment workflow** - an appointment starts as *pending*; the doctor can *confirm* or *reject* it, the
  patient can *cancel* it, and it becomes *completed* once a prescription is written.
- **Video consultations** - confirming a video appointment creates a Jitsi Meet link for both sides.
- **e-Prescriptions** - doctors record the diagnosis, medicines, advice and a follow-up date; patients can print
  the prescription or save it as a PDF.
- **Profiles** - patients store health details (date of birth, blood group, medical history); doctors set their
  fee, working hours and slot length.
- **Admin panel** at `/admin/` for all data, including messages sent through the contact form.

## Tech stack

| Part        | Technology                                   |
|-------------|----------------------------------------------|
| Backend     | Python 3, Django 5.2                         |
| Frontend    | Django templates, Bootstrap 5, Bootstrap Icons |
| Database    | SQLite                                       |
| Video calls | Jitsi Meet (links only, no setup needed)     |
| Hosting     | Vercel (serverless), WhiteNoise for static files |

## Project structure

```
eclinic/                    Project settings, root URLs and WSGI entry point
accounts/                   Custom User model (with a patient/doctor role), sign-up, login and profile pages
clinic/                     Specializations, doctors, patients, appointments, prescriptions, contact messages
  management/commands/
    seed_demo.py            Loads demo specialities, doctors and a patient
  templatetags/clinic_tags.py   Small template filters (form styling, user initials)
  tests.py                  Flow tests for the main user journeys
  test_features.py          Unit, integration and system test cases
templates/                  HTML templates (base layout, accounts, clinic pages)
static/css/style.css        Site styles
requirements.txt            Python dependencies
vercel.json                 Vercel deployment config
```

## Getting started

### Requirements

- Python 3.10 or newer
- Git

### Setup

1. Clone the repository and open the folder:

   ```bash
   git clone https://github.com/arpitt-007/Eclinic.git
   cd Eclinic
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   ```

   - Windows: `.venv\Scripts\activate`
   - macOS / Linux: `source .venv/bin/activate`

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create the database tables:

   ```bash
   python manage.py migrate
   ```

5. (Optional) Load demo data and create an admin account:

   ```bash
   python manage.py seed_demo
   python manage.py createsuperuser
   ```

6. Start the development server:

   ```bash
   python manage.py runserver
   ```

7. Open http://127.0.0.1:8000 in your browser. The admin panel is at http://127.0.0.1:8000/admin/.

### Demo accounts

`seed_demo` creates these accounts. All of them use the password `demo12345`.

| Role    | Usernames                                                        |
|---------|------------------------------------------------------------------|
| Patient | `patient`                                                        |
| Doctor  | `dr_sharma`, `dr_mehta`, `dr_iyer`, `dr_khan`, `dr_reddy`, `dr_bose` |

## How to use

### Patients

1. Click **Sign up** and create a patient account (or log in as `patient`).
2. Open **Find a Doctor**, pick a doctor and click **Book now**.
3. Choose a date and a free time slot, select *Video consultation* or *In-clinic visit*, describe your symptoms
   and click **Confirm booking**.
4. Follow the appointment from your **Dashboard**. Once the doctor confirms it, a **Join video call** button
   appears on the appointment page.
5. After the consultation, open the appointment to view the prescription and use **Print / save as PDF**.

### Doctors

1. Sign up through **Join as a doctor** (or log in as `dr_sharma`).
2. Set your working hours, slot length and fee under **Availability & profile**.
3. Confirm or reject pending requests from your **Dashboard**.
4. After a consultation, open the appointment and write the prescription. Saving it marks the appointment as
   completed.

### Admin

Log in at `/admin/` with a superuser account to manage users, doctors, specialities, appointments, prescriptions
and contact messages. Each speciality has an `icon` field that takes a [Bootstrap Icons](https://icons.getbootstrap.com/)
name such as `heart-pulse`.

## Running the tests

```bash
python manage.py test
```

There are 39 tests in two files:

| File                       | What it covers                                                                  | Tests |
|----------------------------|---------------------------------------------------------------------------------|-------|
| `clinic/tests.py`          | Main user journeys: public pages, sign-up, booking, confirm and prescribe, cancel, access rules | 7 |
| `clinic/test_features.py`  | `UnitTests` - slot generation, age, prescriptions, form validation, double-booking constraint | 14 |
|                            | `IntegrationTests` - meeting links, prescriptions, redirects, search, contact form, dashboards | 8 |
|                            | `SystemTestCases` - end-to-end cases TC01-TC10 (login, booking, confirm, prescribe, cancel) | 10 |

Run a single group with, for example, `python manage.py test clinic.test_features.UnitTests`.

## Configuration

Settings are read from environment variables. None are needed for local development.

| Variable                      | Purpose                                                            |
|-------------------------------|--------------------------------------------------------------------|
| `DJANGO_SECRET_KEY`           | Secret key. Required whenever debug mode is off.                   |
| `DJANGO_DEBUG`                | `1` to turn debug on, `0` to turn it off. Defaults to on locally.  |
| `DJANGO_ALLOWED_HOSTS`        | Comma-separated host names, e.g. `example.com`.                    |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma-separated origins, e.g. `https://example.com`.               |
| `ADMIN_PASSWORD`              | If set, `seed_demo` creates (or updates) an `admin` superuser with this password. |

For a normal production server, set `DJANGO_DEBUG=0`, a secret key and your host names, run
`python manage.py collectstatic`, and serve the app with Gunicorn.

## Deploying to Vercel

The project runs on Vercel as a serverless Python function (`vercel.json` points to `eclinic/wsgi.py`). There is
no database server: on every cold start the app creates a fresh SQLite file in `/tmp` and loads the demo accounts
from `seed_demo.py`. Logins are kept in signed cookies and WhiteNoise serves the static files.

1. Push the repository to GitHub and import it at https://vercel.com/new (framework preset: **Other**), or run
   `vercel --prod` in the project folder.
2. In the Vercel project, open **Settings**, then **Environment Variables**, and add:
   - `DJANGO_SECRET_KEY` - required, a long random string
   - `ADMIN_PASSWORD` - optional, the password for the built-in `admin` account
3. Redeploy so the variables take effect.

To add or change accounts on the live site, edit the `DOCTORS` list or the patient block in `seed_demo.py` and push.

**Note:** bookings, sign-ups and profile changes made on the live Vercel site are temporary. Each serverless
instance keeps its own copy of the data, which is reset on every cold start and redeploy, and uploaded doctor
photos are not kept. Use a hosted database (such as PostgreSQL) and file storage if data needs to persist.

## Troubleshooting

- **Speciality icons look broken after updating the code:** run `python manage.py migrate`. Older versions
  stored emojis in the speciality `icon` field, and migration `0002` converts them to icon names.
- **"Set the DJANGO_SECRET_KEY environment variable" error:** debug mode is off, so a secret key is required.
  Set `DJANGO_SECRET_KEY`, or set `DJANGO_DEBUG=1` for local testing.
