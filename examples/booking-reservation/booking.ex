# Generated from: booking-reservation.tundra
# Language: Elixir (standard library only)
#
# Mapping:
#   States      -> atoms
#   Processes   -> functions returning {:ok, state} | {:error, contract}
#   Contracts   -> checked explicitly; fail fast with the Contract text
#   Decorators  -> encoded as guards on time arguments

defmodule Booking do
  @moduledoc """
  Thin implementation of the Tundra model "Booking and reservation".
  """

  defmodule ContractViolation do
    defexception [:message]

    @impl true
    def exception(msg) when is_binary(msg), do: %__MODULE__{message: msg}
  end

  # ------------------------------------------------------------------
  # States (atoms) – subject is always explicit in the name
  # ------------------------------------------------------------------

  @type time_slot_state :: :available | :reserved
  @type reservation_state ::
          :pending
          | :confirmed
          | :cancelled_by_guest
          | :cancelled_by_host
          | :completed
          | :no_show

  @type reservation :: %{
          state: reservation_state(),
          guest_id: term(),
          start_time: DateTime.t(),
          end_time: DateTime.t(),
          created_at: DateTime.t()
        }

  @type time_slot :: %{
          state: time_slot_state(),
          capacity: pos_integer(),
          start_time: DateTime.t(),
          end_time: DateTime.t()
        }

  # ------------------------------------------------------------------
  # Processes
  # ------------------------------------------------------------------

  @doc "Check availability – Time slot is Available (capacity 1)."
  def check_availability(%{state: :available, capacity: cap}) when cap >= 1, do: {:ok, :available}
  def check_availability(%{state: :reserved}), do: {:ok, :reserved}
  def check_availability(_), do: {:error, "Time slot is not available"}

  @doc """
  Create Reservation.
  Contract: A Reservation may be created only for a time slot that is Available.
  """
  def create_reservation(%{state: :available} = slot, guest_id, now \\ DateTime.utc_now()) do
    reservation = %{
      state: :pending,
      guest_id: guest_id,
      start_time: slot.start_time,
      end_time: slot.end_time,
      created_at: now
    }

    new_slot = %{slot | state: :reserved}
    {:ok, %{reservation: reservation, time_slot: new_slot}}
  end

  def create_reservation(%{state: :reserved}, _guest_id, _now) do
    {:error,
     "A Reservation may be created only for a time slot that is Available"}
  end

  @doc "Confirm Reservation – Pending → Confirmed."
  def confirm_reservation(%{state: :pending} = res) do
    {:ok, %{res | state: :confirmed}}
  end

  def confirm_reservation(%{state: state}) do
    {:error, "Reservation can only be confirmed while Pending (was #{state})"}
  end

  @doc """
  Cancel by Guest.
  Contracts:
    - Only the Guest who created a Reservation may cancel it while it is Confirmed
    - A Guest may cancel a Confirmed Reservation only more than 24 hours before start time
  Decorators: @before start time, @within 24 hours before start
  """
  def cancel_by_guest(%{state: :confirmed, guest_id: owner} = res, actor_id, now \\ DateTime.utc_now()) do
    cond do
      actor_id != owner ->
        {:error,
         "Only the Guest who created a Reservation may cancel it while it is Confirmed"}

      not before_start?(res, now) ->
        {:error, "A Host may cancel a Reservation only before the start time"}

      not more_than_24h_before?(res, now) ->
        {:error,
         "A Guest may cancel a Confirmed Reservation only more than 24 hours before start time"}

      true ->
        {:ok, %{res | state: :cancelled_by_guest}}
    end
  end

  def cancel_by_guest(%{state: state}, _actor_id, _now) do
    {:error, "Guest may only cancel a Confirmed Reservation (was #{state})"}
  end

  @doc """
  Cancel by Host.
  Contract: A Host may cancel a Reservation only before the start time.
  Decorator: @before start time
  """
  def cancel_by_host(%{state: state} = res, now \\ DateTime.utc_now())
      when state in [:pending, :confirmed] do
    if before_start?(res, now) do
      {:ok, %{res | state: :cancelled_by_host}}
    else
      {:error, "A Host may cancel a Reservation only before the start time"}
    end
  end

  def cancel_by_host(%{state: :completed}, _now) do
    {:error, "Once a Reservation is Completed it cannot be cancelled"}
  end

  def cancel_by_host(%{state: state}, _now) do
    {:error, "Host cannot cancel a Reservation in state #{state}"}
  end

  @doc """
  Mark as Completed.
  Decorator: @after end time
  """
  def mark_as_completed(%{state: :confirmed} = res, now \\ DateTime.utc_now()) do
    if after_end?(res, now) do
      {:ok, %{res | state: :completed}}
    else
      {:error, "Reservation can only be completed after end time"}
    end
  end

  def mark_as_completed(%{state: state}, _now) do
    {:error, "Only a Confirmed Reservation can be completed (was #{state})"}
  end

  @doc """
  Mark as No-show.
  Contract: The System marks a Reservation as No-show if the Guest does not arrive by start time.
  Decorator: @after start time
  """
  def mark_as_no_show(%{state: :confirmed} = res, now \\ DateTime.utc_now()) do
    if after_start?(res, now) do
      {:ok, %{res | state: :no_show}}
    else
      {:error, "No-show can only be marked after start time"}
    end
  end

  def mark_as_no_show(%{state: state}, _now) do
    {:error, "Only a Confirmed Reservation can become No-show (was #{state})"}
  end

  # ------------------------------------------------------------------
  # Temporal helpers (decorators)
  # ------------------------------------------------------------------

  defp before_start?(%{start_time: start}, now), do: DateTime.compare(now, start) == :lt
  defp after_start?(%{start_time: start}, now), do: DateTime.compare(now, start) != :lt
  defp after_end?(%{end_time: end_t}, now), do: DateTime.compare(now, end_t) != :lt

  defp more_than_24h_before?(%{start_time: start}, now) do
    hours = DateTime.diff(start, now, :hour)
    hours > 24
  end
end
