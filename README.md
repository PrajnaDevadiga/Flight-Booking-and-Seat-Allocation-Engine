# Flight Booking & Seat Allocation Engine

Python application to:
- validate booking data
- allocate seats based on availability
- generate booking and flight summary reports
- run unit tests for key booking scenarios

## Validation Rules

- Flight must exist
- `seats_booked` must be greater than 0
- `booking_date` must be a valid date in `YYYY-MM-DD` format

## Seat Allocation Rules

- If `seats_booked <= available seats` -> `CONFIRMED`
- If `seats_booked > available seats` -> `WAITLIST`

## Input Files

- `flights.csv`
- `flight_bookings.csv`

## Output Files

- `booking_status_report.csv`
- `flight_seat_summary.csv`

## How to Run

From the project folder:

```bash
python booking_engine.py
```

This generates:
- `booking_status_report.csv`
- `flight_seat_summary.csv`

## Run Unit Tests

```bash
python -m unittest -v
```

Included test cases:
- `test_invalid_flight_rejected`
- `test_negative_seats_rejected`
- `test_seat_allocation`
- `test_waitlist_logic`
- `test_remaining_seats_calculation`
- `test_invalid_date_rejected`
- `test_invalid_non_numeric_seats_rejected`
- `test_report_writers_and_run_engine`

## Coverage (minimum 80%)

The project includes `.coveragerc` with `fail_under = 80`.

Run coverage and generate detailed reports:

```bash
python -m coverage erase
python -m coverage run -m unittest -v
python -m coverage report -m
python -m coverage html
python -m coverage xml -o coverage.xml
python -m coverage json -o coverage.json
```

## Dashboard 

```bash
streamlit run app.py
```

Detailed outputs:
- Terminal report with missing lines (`coverage report -m`)
- Interactive HTML report at `htmlcov/index.html`
- Machine-readable reports: `coverage.xml`, `coverage.json`
