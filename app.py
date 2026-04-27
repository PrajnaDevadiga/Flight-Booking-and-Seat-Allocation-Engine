from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


BOOKING_REPORT_PATH = Path("booking_status_report.csv")
SEAT_SUMMARY_PATH = Path("flight_seat_summary.csv")

STATUS_COLORS = {
    "CONFIRMED": "#16A34A",
    "WAITLIST": "#F97316",
    "REJECTED": "#DC2626",
}


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    bookings = pd.read_csv(BOOKING_REPORT_PATH)
    summary = pd.read_csv(SEAT_SUMMARY_PATH)

    bookings["seats_booked"] = pd.to_numeric(bookings["seats_booked"], errors="coerce").fillna(0)
    bookings["booking_date_parsed"] = pd.to_datetime(
        bookings["booking_date"], errors="coerce", format="%Y-%m-%d"
    )

    summary["seat_capacity"] = pd.to_numeric(summary["seat_capacity"], errors="coerce").fillna(0)
    summary["remaining_seats"] = pd.to_numeric(summary["remaining_seats"], errors="coerce").fillna(0)
    summary["booked_seats"] = summary["seat_capacity"] - summary["remaining_seats"]

    return bookings, summary


def apply_filters(
    bookings: pd.DataFrame,
    selected_flights: list[str],
    selected_statuses: list[str],
    date_range: tuple[pd.Timestamp, pd.Timestamp] | None,
    search_text: str,
) -> pd.DataFrame:
    filtered = bookings.copy()

    if selected_flights:
        filtered = filtered[filtered["flight_id"].isin(selected_flights)]

    if selected_statuses:
        filtered = filtered[filtered["booking_status"].isin(selected_statuses)]

    if date_range:
        start_date, end_date = date_range
        valid_dates = filtered["booking_date_parsed"].notna()
        filtered = filtered[
            valid_dates
            & (filtered["booking_date_parsed"] >= pd.Timestamp(start_date))
            & (filtered["booking_date_parsed"] <= pd.Timestamp(end_date))
        ]

    if search_text:
        search_mask = (
            filtered["booking_id"].astype(str).str.contains(search_text, case=False, na=False)
            | filtered["user_id"].astype(str).str.contains(search_text, case=False, na=False)
            | filtered["flight_id"].astype(str).str.contains(search_text, case=False, na=False)
        )
        filtered = filtered[search_mask]

    return filtered


def kpi_card(label: str, value: str, color: str) -> None:
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #111827 0%, #1F2937 100%);
            border-left: 5px solid {color};
            border-radius: 12px;
            padding: 14px 16px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.15);
            min-height: 96px;">
            <div style="font-size: 13px; color: #D1D5DB; margin-bottom: 8px;">{label}</div>
            <div style="font-size: 30px; font-weight: 700; color: #F9FAFB;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_capacity_table(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    def row_style(row: pd.Series) -> list[str]:
        low_capacity = (
            row["seat_capacity"] > 0 and row["remaining_seats"] / row["seat_capacity"] <= 0.15
        )
        high_waitlist = row["waitlisted_bookings"] >= 2

        styles = []
        for _ in row.index:
            if high_waitlist:
                styles.append("background-color: #FFF1F2; color: #B91C1C;")
            elif low_capacity:
                styles.append("background-color: #FFF7ED; color: #9A3412;")
            else:
                styles.append("")
        return styles

    return df.style.apply(row_style, axis=1)


def main() -> None:
    st.set_page_config(
        page_title="Flight Booking Dashboard",
        page_icon="✈️",
        layout="wide",
    )

    st.title("✈️ Flight Booking & Seat Allocation Dashboard")
    st.caption("Monitor bookings, waitlists, and flight seat capacity in real time.")

    if not BOOKING_REPORT_PATH.exists() or not SEAT_SUMMARY_PATH.exists():
        st.error(
            "Required report files are missing. Please run `python booking_engine.py` first to generate input CSVs."
        )
        st.stop()

    bookings, summary = load_data()

    flight_options = sorted(summary["flight_id"].dropna().astype(str).unique().tolist())
    status_options = sorted(bookings["booking_status"].dropna().astype(str).unique().tolist())

    valid_booking_dates = bookings["booking_date_parsed"].dropna()
    default_date_range = None
    if not valid_booking_dates.empty:
        default_date_range = (valid_booking_dates.min().date(), valid_booking_dates.max().date())

    with st.sidebar:
        st.header("Filters & Navigation")
        selected_flights = st.multiselect(
            "Filter by Flight ID",
            options=flight_options,
            placeholder="Choose one or more flights",
        )
        selected_statuses = st.multiselect(
            "Filter by Booking Status",
            options=status_options,
            default=[status for status in status_options if status in ("CONFIRMED", "WAITLIST")],
        )
        search_text = st.text_input("Search Booking / User / Flight", "")

        date_range = None
        if default_date_range:
            date_range = st.date_input(
                "Booking Date Range",
                value=default_date_range,
                min_value=default_date_range[0],
                max_value=default_date_range[1],
            )
            if isinstance(date_range, tuple) and len(date_range) == 2:
                date_range = (pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]))
            else:
                date_range = None

    filtered_bookings = apply_filters(
        bookings=bookings,
        selected_flights=selected_flights,
        selected_statuses=selected_statuses,
        date_range=date_range,
        search_text=search_text.strip(),
    )

    # KPI section
    total_flights = int(summary["flight_id"].nunique())
    total_bookings = int(len(filtered_bookings))
    confirmed_bookings = int((filtered_bookings["booking_status"] == "CONFIRMED").sum())
    waitlisted_bookings = int((filtered_bookings["booking_status"] == "WAITLIST").sum())
    total_remaining_seats = int(summary["remaining_seats"].sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("Total Flights", f"{total_flights}", "#3B82F6")
    with c2:
        kpi_card("Total Bookings (Filtered)", f"{total_bookings}", "#A855F7")
    with c3:
        kpi_card("Confirmed Bookings", f"{confirmed_bookings}", STATUS_COLORS["CONFIRMED"])
    with c4:
        kpi_card("Waitlisted Bookings", f"{waitlisted_bookings}", STATUS_COLORS["WAITLIST"])
    with c5:
        kpi_card("Seats Remaining", f"{total_remaining_seats}", "#06B6D4")

    st.markdown("---")

    # Flight search and detail section
    st.subheader("Flight Search & Filter")
    selected_flight = st.selectbox(
        "Select Flight ID to inspect details",
        options=[""] + flight_options,
        format_func=lambda x: "Select a flight" if x == "" else x,
    )

    if selected_flight:
        flight_row = summary[summary["flight_id"] == selected_flight]
        flight_bookings = bookings[bookings["flight_id"] == selected_flight]

        if flight_row.empty:
            st.warning("No record found for this flight.")
        else:
            row = flight_row.iloc[0]
            confirmed_count = int((flight_bookings["booking_status"] == "CONFIRMED").sum())
            waitlist_count = int((flight_bookings["booking_status"] == "WAITLIST").sum())

            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Airline", row["airline"])
            d2.metric("Route", f"{row['source']} → {row['destination']}")
            d3.metric("Total Seats", int(row["seat_capacity"]))
            d4.metric("Remaining Seats", int(row["remaining_seats"]))

            status_dist = pd.DataFrame(
                {
                    "status": ["CONFIRMED", "WAITLIST"],
                    "count": [confirmed_count, waitlist_count],
                }
            )
            detail_chart = px.pie(
                status_dist,
                names="status",
                values="count",
                title=f"Booking Status Distribution for {selected_flight}",
                color="status",
                color_discrete_map=STATUS_COLORS,
                hole=0.4,
            )
            detail_chart.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(detail_chart, use_container_width=True)
    else:
        st.info("Select a flight to view details and booking status split.")

    st.markdown("---")

    # Seat allocation insights
    st.subheader("Seat Allocation Insights")
    per_flight_status = (
        bookings[bookings["booking_status"].isin(["CONFIRMED", "WAITLIST"])]
        .groupby(["flight_id", "booking_status"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
    )

    if per_flight_status.empty:
        st.warning("No confirmed/waitlisted booking records available for charting.")
    else:
        allocation_chart = px.bar(
            per_flight_status,
            x="flight_id",
            y="count",
            color="booking_status",
            barmode="group",
            title="Confirmed vs Waitlisted Bookings per Flight",
            color_discrete_map=STATUS_COLORS,
            text_auto=True,
            hover_data={"count": True},
        )
        st.plotly_chart(allocation_chart, use_container_width=True)

    fully_booked = summary[summary["remaining_seats"] <= 0]["flight_id"].tolist()
    waitlist_counts = (
        bookings[bookings["booking_status"] == "WAITLIST"]
        .groupby("flight_id")
        .size()
        .sort_values(ascending=False)
    )
    high_waitlist = waitlist_counts[waitlist_counts >= 2].index.tolist()

    a1, a2 = st.columns(2)
    with a1:
        if fully_booked:
            st.error(f"Fully booked flights: {', '.join(fully_booked)}")
        else:
            st.success("No fully booked flights right now.")
    with a2:
        if high_waitlist:
            st.warning(f"High waitlist flights: {', '.join(high_waitlist)}")
        else:
            st.info("No high waitlist flights detected.")

    st.markdown("---")

    # Booking trends
    st.subheader("Booking Trends")
    trend_df = filtered_bookings[filtered_bookings["booking_date_parsed"].notna()].copy()
    trend_df["booking_day"] = trend_df["booking_date_parsed"].dt.date
    trend_agg = trend_df.groupby("booking_day", as_index=False).size().rename(columns={"size": "bookings"})

    if trend_agg.empty:
        st.warning("No valid-dated bookings available for trend analysis in selected filters.")
    else:
        trend_chart = px.line(
            trend_agg,
            x="booking_day",
            y="bookings",
            markers=True,
            title="Bookings Over Time",
            hover_data={"bookings": True},
        )
        trend_chart.update_traces(line=dict(color="#2563EB", width=3))
        st.plotly_chart(trend_chart, use_container_width=True)

    st.markdown("---")

    # Flight capacity analysis
    st.subheader("Flight Capacity Analysis")
    waitlist_per_flight = (
        bookings[bookings["booking_status"] == "WAITLIST"]
        .groupby("flight_id")
        .size()
        .rename("waitlisted_bookings")
    )
    capacity_df = summary.merge(waitlist_per_flight, on="flight_id", how="left")
    capacity_df["waitlisted_bookings"] = capacity_df["waitlisted_bookings"].fillna(0).astype(int)
    capacity_df = capacity_df[
        [
            "flight_id",
            "seat_capacity",
            "booked_seats",
            "remaining_seats",
            "waitlisted_bookings",
            "airline",
            "source",
            "destination",
        ]
    ].sort_values("remaining_seats")

    st.dataframe(style_capacity_table(capacity_df), use_container_width=True)

    # Optional advanced section
    st.subheader("Busiest Flights")
    busiest = (
        bookings[bookings["booking_status"] == "CONFIRMED"]
        .groupby("flight_id")
        .size()
        .sort_values(ascending=False)
        .head(5)
        .reset_index(name="confirmed_bookings")
    )
    if busiest.empty:
        st.info("No confirmed bookings available to compute busiest flights.")
    else:
        busiest_chart = px.bar(
            busiest,
            x="flight_id",
            y="confirmed_bookings",
            title="Top 5 Busiest Flights (by Confirmed Bookings)",
            text_auto=True,
            color_discrete_sequence=["#0EA5E9"],
            hover_data={"confirmed_bookings": True},
        )
        st.plotly_chart(busiest_chart, use_container_width=True)

    st.markdown("---")

    # Raw table section
    st.subheader("Data Tables")
    t1, t2 = st.tabs(["Booking Status Report", "Flight Seat Summary"])

    with t1:
        st.dataframe(filtered_bookings, use_container_width=True)
        booking_csv = filtered_bookings.drop(columns=["booking_date_parsed"]).to_csv(index=False)
        st.download_button(
            label="Download Filtered Booking Report",
            data=booking_csv,
            file_name="filtered_booking_status_report.csv",
            mime="text/csv",
        )

    with t2:
        summary_filtered = summary.copy()
        if selected_flights:
            summary_filtered = summary_filtered[summary_filtered["flight_id"].isin(selected_flights)]
        st.dataframe(summary_filtered, use_container_width=True)
        st.download_button(
            label="Download Flight Seat Summary",
            data=summary_filtered.to_csv(index=False),
            file_name="filtered_flight_seat_summary.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
