# SmartPark Kenya - Web-Based Parking Management System

A simple web-based parking management system developed for the MMU Actual System Development assignment.

## Features

- Displays all parking slots and their availability.
- Automatically assigns the first available slot to an arriving vehicle.
- Records vehicle registration, driver name and entry time.
- Prevents the same vehicle from being entered twice while it is parked.
- Calculates parking duration automatically when the vehicle exits.
- Calculates fees using the assignment rates.
- Records payment/exit and makes the slot available again.
- Uses SQLite for persistent data storage.
- Responsive web interface for computers and phones.
- Includes a JSON status endpoint at `/api/status`.

## Parking rates

| Duration | Fee |
|---|---:|
| 0-30 minutes | Free |
| Up to 2 hours | KSh 50 |
| Up to 4 hours | KSh 100 |
| Up to 6 hours | KSh 300 |
| Over 6 hours | KSh 500 |

## How to run

1. Install Python 3 on the computer.
2. Open this folder in VS Code.
3. Open the VS Code terminal.
4. Run:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

If `python` does not work, try `py`.

5. Install Flask:

```bash
pip install -r requirements.txt
```

6. Start the application:

```bash
python app.py
```

7. Open the address shown in the terminal, normally:

http://127.0.0.1:5000

The SQLite database `parking.db` is created automatically the first time the program runs.

## Suggested project explanation

The project has three main parts:

- `app.py`: Python/Flask backend. Handles vehicle entry, exit, fee calculation and database operations.
- `templates/dashboard.html`: Website structure and forms.
- `static/style.css`: Website design.
- `static/script.js`: Small browser-side enhancement.
- `parking.db`: SQLite database created automatically.

## Important

This is an academic/demo system. Real automatic barriers, M-Pesa payment APIs, CCTV/ANPR cameras and authentication would require additional hardware/services and security controls.
