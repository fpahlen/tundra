# Executable Scenarios for booking-reservation.tundra
# Run with: elixir booking_scenarios.exs
#
# Each Scenario from the Tundra model becomes a readable function.
# Happy paths must succeed; error paths must surface the correct Contract.

Code.require_file("booking.ex")

defmodule BookingScenarios do
  @moduledoc false

  def run_all do
    IO.puts("Running Booking Tundra scenarios...\n")

    happy_path_guest_books_and_stays()
    error_guest_tries_to_book_reserved_slot()
    error_guest_cancels_too_late()
    error_guest_does_not_arrive()

    IO.puts("\nAll scenarios completed.")
  end

  # ------------------------------------------------------------------
  # Scenario: Happy path – guest books and stays
  # ------------------------------------------------------------------
  def happy_path_guest_books_and_stays do
    IO.puts("Scenario: Happy path – guest books and stays")

    start = hours_from_now(48)
    end_t = hours_from_now(50)

    slot = %{state: :available, capacity: 1, start_time: start, end_time: end_t}

    # When the Guest creates a Reservation
    {:ok, %{reservation: res, time_slot: slot}} = Booking.create_reservation(slot, "guest-1")
    assert res.state == :pending, "Then the Reservation is Pending"
    assert slot.state == :reserved, "And the Time slot is Reserved"
    IO.puts("  ✓ Create Reservation → Pending, slot Reserved")

    # When the Reservation is confirmed
    {:ok, res} = Booking.confirm_reservation(res)
    assert res.state == :confirmed, "Then the Reservation is Confirmed"
    IO.puts("  ✓ Confirm Reservation → Confirmed")

    # When the stay finishes successfully (after end time)
    after_end = hours_from_now(51)
    {:ok, res} = Booking.mark_as_completed(res, after_end)
    assert res.state == :completed, "Then the Reservation is Completed"
    IO.puts("  ✓ Mark as Completed → Completed")
    IO.puts("  Happy path passed.\n")
  end

  # ------------------------------------------------------------------
  # Scenario: Error – guest tries to book an already reserved slot
  # ------------------------------------------------------------------
  def error_guest_tries_to_book_reserved_slot do
    IO.puts("Scenario: Error – guest tries to book an already reserved slot")

    start = hours_from_now(48)
    end_t = hours_from_now(50)
    slot = %{state: :reserved, capacity: 1, start_time: start, end_time: end_t}

    result = Booking.create_reservation(slot, "guest-2")

    case result do
      {:error, msg} ->
        expected = "A Reservation may be created only for a time slot that is Available"
        assert msg == expected, "Expected contract: #{expected}"
        IO.puts("  ✓ Rejected with correct Contract")
        IO.puts("  Error scenario passed.\n")

      {:ok, _} ->
        raise "Expected contract violation, but reservation was created"
    end
  end

  # ------------------------------------------------------------------
  # Scenario: Error – guest cancels too late
  # ------------------------------------------------------------------
  def error_guest_cancels_too_late do
    IO.puts("Scenario: Error – guest cancels too late")

    # start time less than 24 hours away
    start = hours_from_now(10)
    end_t = hours_from_now(12)

    res = %{
      state: :confirmed,
      guest_id: "guest-1",
      start_time: start,
      end_time: end_t,
      created_at: hours_from_now(-1)
    }

    result = Booking.cancel_by_guest(res, "guest-1", hours_from_now(0))

    case result do
      {:error, msg} ->
        expected =
          "A Guest may cancel a Confirmed Reservation only more than 24 hours before start time"

        assert msg == expected, "Expected contract: #{expected}"
        IO.puts("  ✓ Rejected with correct Contract")
        IO.puts("  Error scenario passed.\n")

      {:ok, _} ->
        raise "Expected contract violation, but cancellation succeeded"
    end
  end

  # ------------------------------------------------------------------
  # Scenario: Error – guest does not arrive
  # ------------------------------------------------------------------
  def error_guest_does_not_arrive do
    IO.puts("Scenario: Error – guest does not arrive")

    start = hours_from_now(-1)
    end_t = hours_from_now(1)

    res = %{
      state: :confirmed,
      guest_id: "guest-1",
      start_time: start,
      end_time: end_t,
      created_at: hours_from_now(-48)
    }

    {:ok, res} = Booking.mark_as_no_show(res, hours_from_now(0))
    assert res.state == :no_show, "Then the Reservation is No-show"
    IO.puts("  ✓ Mark as No-show → No-show")
    IO.puts("  Scenario passed.\n")
  end

  # ------------------------------------------------------------------
  # Helpers
  # ------------------------------------------------------------------

  defp hours_from_now(h) do
    DateTime.utc_now() |> DateTime.add(h * 3600, :second)
  end

  defp assert(true, _msg), do: :ok
  defp assert(false, msg), do: raise("Assertion failed: #{msg}")
end

BookingScenarios.run_all()
