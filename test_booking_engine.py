import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from booking_engine import (
    process_bookings,
    run_engine,
    write_booking_status_report,
    write_flight_seat_summary,
)


class TestBookingEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.booking_results, cls.summary_rows = process_bookings(
            "flights.csv", "flight_bookings.csv"
        )
        cls.results_by_booking_id = {
            result.booking_id: result for result in cls.booking_results
        }
        cls.summary_by_flight_id = {
            row["flight_id"]: row for row in cls.summary_rows
        }

    def test_invalid_flight_rejected(self) -> None:
        result = self.results_by_booking_id["B007"]
        self.assertEqual(result.booking_status, "REJECTED")
        self.assertIn("Flight does not exist", result.error_message)

    def test_negative_seats_rejected(self) -> None:
        result = self.results_by_booking_id["B006"]
        self.assertEqual(result.booking_status, "REJECTED")
        self.assertIn("greater than 0", result.error_message)

    def test_seat_allocation(self) -> None:
        result = self.results_by_booking_id["B001"]
        self.assertEqual(result.booking_status, "CONFIRMED")

    def test_waitlist_logic(self) -> None:
        result = self.results_by_booking_id["B004"]
        self.assertEqual(result.booking_status, "WAITLIST")
        self.assertIn("Insufficient seats", result.error_message)

    def test_invalid_date_rejected(self) -> None:
        result = self.results_by_booking_id["B008"]
        self.assertEqual(result.booking_status, "REJECTED")
        self.assertIn("Invalid booking_date", result.error_message)

    def test_remaining_seats_calculation(self) -> None:
        self.assertEqual(self.summary_by_flight_id["F001"]["remaining_seats"], 178)
        self.assertEqual(self.summary_by_flight_id["F002"]["remaining_seats"], 119)
        self.assertEqual(self.summary_by_flight_id["F003"]["remaining_seats"], 146)
        self.assertEqual(self.summary_by_flight_id["F004"]["remaining_seats"], 194)
        self.assertEqual(self.summary_by_flight_id["F005"]["remaining_seats"], 90)

    def test_invalid_non_numeric_seats_rejected(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            flights_path = temp / "flights.csv"
            bookings_path = temp / "flight_bookings.csv"

            flights_path.write_text(
                "flight_id,airline,source,destination,seat_capacity\n"
                "F100,DemoAir,A,B,10\n",
                encoding="utf-8",
            )
            bookings_path.write_text(
                "booking_id,flight_id,user_id,seats_booked,booking_date\n"
                "B100,F100,U100,abc,2024-11-01\n",
                encoding="utf-8",
            )

            booking_results, _ = process_bookings(flights_path, bookings_path)
            self.assertEqual(booking_results[0].booking_status, "REJECTED")
            self.assertIn("Invalid seats_booked value", booking_results[0].error_message)

    def test_report_writers_and_run_engine(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            flights_path = temp / "flights.csv"
            bookings_path = temp / "flight_bookings.csv"
            booking_report_path = temp / "booking_status_report.csv"
            summary_report_path = temp / "flight_seat_summary.csv"

            flights_path.write_text(
                "flight_id,airline,source,destination,seat_capacity\n"
                "F200,DemoAir,A,B,5\n",
                encoding="utf-8",
            )
            bookings_path.write_text(
                "booking_id,flight_id,user_id,seats_booked,booking_date\n"
                "B200,F200,U200,2,2024-11-01\n",
                encoding="utf-8",
            )

            booking_results, summary_rows = run_engine(
                flights_path,
                bookings_path,
                booking_report_path,
                summary_report_path,
            )
            self.assertEqual(booking_results[0].booking_status, "CONFIRMED")
            self.assertEqual(summary_rows[0]["remaining_seats"], 3)
            self.assertTrue(booking_report_path.exists())
            self.assertTrue(summary_report_path.exists())

            # Exercise writer helpers directly as well.
            second_booking_report = temp / "booking_status_report_2.csv"
            second_summary_report = temp / "flight_seat_summary_2.csv"
            write_booking_status_report(booking_results, second_booking_report)
            write_flight_seat_summary(summary_rows, second_summary_report)
            self.assertTrue(second_booking_report.exists())
            self.assertTrue(second_summary_report.exists())


if __name__ == "__main__":
    unittest.main()
