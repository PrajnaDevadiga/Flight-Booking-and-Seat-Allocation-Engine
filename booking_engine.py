from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class FlightRecord:
    flight_id: str
    airline: str
    source: str
    destination: str
    seat_capacity: int


@dataclass
class BookingResult:
    booking_id: str
    flight_id: str
    user_id: str
    seats_booked: int
    booking_date: str
    booking_status: str
    error_message: str


def _is_valid_date(date_value: str) -> bool:
    try:
        datetime.strptime(date_value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def load_flights(flights_csv_path: str | Path) -> Dict[str, FlightRecord]:
    flights: Dict[str, FlightRecord] = {}
    with open(flights_csv_path, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            flight = FlightRecord(
                flight_id=row["flight_id"],
                airline=row["airline"],
                source=row["source"],
                destination=row["destination"],
                seat_capacity=int(row["seat_capacity"]),
            )
            flights[flight.flight_id] = flight
    return flights


def process_bookings(
    flights_csv_path: str | Path,
    bookings_csv_path: str | Path,
) -> Tuple[List[BookingResult], List[dict]]:
    flights = load_flights(flights_csv_path)
    remaining_seats = {
        flight_id: flight.seat_capacity for flight_id, flight in flights.items()
    }
    bookings_report: List[BookingResult] = []

    with open(bookings_csv_path, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            booking_id = row["booking_id"]
            flight_id = row["flight_id"]
            user_id = row["user_id"]
            booking_date = row["booking_date"]

            try:
                seats_booked = int(row["seats_booked"])
            except (TypeError, ValueError):
                bookings_report.append(
                    BookingResult(
                        booking_id=booking_id,
                        flight_id=flight_id,
                        user_id=user_id,
                        seats_booked=0,
                        booking_date=booking_date,
                        booking_status="REJECTED",
                        error_message="Invalid seats_booked value",
                    )
                )
                continue

            if flight_id not in flights:
                bookings_report.append(
                    BookingResult(
                        booking_id=booking_id,
                        flight_id=flight_id,
                        user_id=user_id,
                        seats_booked=seats_booked,
                        booking_date=booking_date,
                        booking_status="REJECTED",
                        error_message="Flight does not exist",
                    )
                )
                continue

            if seats_booked <= 0:
                bookings_report.append(
                    BookingResult(
                        booking_id=booking_id,
                        flight_id=flight_id,
                        user_id=user_id,
                        seats_booked=seats_booked,
                        booking_date=booking_date,
                        booking_status="REJECTED",
                        error_message="seats_booked must be greater than 0",
                    )
                )
                continue

            if not _is_valid_date(booking_date):
                bookings_report.append(
                    BookingResult(
                        booking_id=booking_id,
                        flight_id=flight_id,
                        user_id=user_id,
                        seats_booked=seats_booked,
                        booking_date=booking_date,
                        booking_status="REJECTED",
                        error_message="Invalid booking_date",
                    )
                )
                continue

            if seats_booked <= remaining_seats[flight_id]:
                remaining_seats[flight_id] -= seats_booked
                status = "CONFIRMED"
                error = ""
            else:
                status = "WAITLIST"
                error = "Insufficient seats available"

            bookings_report.append(
                BookingResult(
                    booking_id=booking_id,
                    flight_id=flight_id,
                    user_id=user_id,
                    seats_booked=seats_booked,
                    booking_date=booking_date,
                    booking_status=status,
                    error_message=error,
                )
            )

    summary_rows = []
    for flight_id, flight in flights.items():
        summary_rows.append(
            {
                "flight_id": flight.flight_id,
                "airline": flight.airline,
                "source": flight.source,
                "destination": flight.destination,
                "seat_capacity": flight.seat_capacity,
                "remaining_seats": remaining_seats[flight_id],
            }
        )

    return bookings_report, summary_rows


def write_booking_status_report(
    booking_results: List[BookingResult], output_path: str | Path
) -> None:
    fieldnames = [
        "booking_id",
        "flight_id",
        "user_id",
        "seats_booked",
        "booking_date",
        "booking_status",
        "error_message",
    ]
    with open(output_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in booking_results:
            writer.writerow(
                {
                    "booking_id": result.booking_id,
                    "flight_id": result.flight_id,
                    "user_id": result.user_id,
                    "seats_booked": result.seats_booked,
                    "booking_date": result.booking_date,
                    "booking_status": result.booking_status,
                    "error_message": result.error_message,
                }
            )


def write_flight_seat_summary(summary_rows: List[dict], output_path: str | Path) -> None:
    fieldnames = [
        "flight_id",
        "airline",
        "source",
        "destination",
        "seat_capacity",
        "remaining_seats",
    ]
    with open(output_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)


def run_engine(
    flights_csv_path: str | Path = "flights.csv",
    bookings_csv_path: str | Path = "flight_bookings.csv",
    booking_report_path: str | Path = "booking_status_report.csv",
    seat_summary_path: str | Path = "flight_seat_summary.csv",
) -> Tuple[List[BookingResult], List[dict]]:
    booking_results, summary_rows = process_bookings(flights_csv_path, bookings_csv_path)
    write_booking_status_report(booking_results, booking_report_path)
    write_flight_seat_summary(summary_rows, seat_summary_path)
    return booking_results, summary_rows


if __name__ == "__main__":
    run_engine()
