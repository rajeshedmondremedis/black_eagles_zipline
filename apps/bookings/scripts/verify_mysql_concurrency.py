"""
Standalone verification script to test concurrent booking protection directly
against MySQL with the InnoDB storage engine.
"""
import os
import sys
import django
import threading
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.bookings.models import Booking, BookingSlot
from apps.bookings.services import create_booking_atomic

def run_mysql_audit():
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION(), @@default_storage_engine;")
        db_version, engine = cursor.fetchone()
        cursor.execute("SELECT DATABASE();")
        active_db = cursor.fetchone()[0]

    print(f"==================================================")
    print(f"DATABASE ENGINE AUDIT:")
    print(f"Active Database: {active_db}")
    print(f"Server Version: {db_version}")
    print(f"Storage Engine: {engine}")
    print(f"==================================================")

    # 1. Setup slot with capacity 6
    slot, _ = BookingSlot.objects.update_or_create(
        order=99,
        defaults={
            'name': 'Audit Concurrency Slot',
            'start_time': datetime.time(10, 0),
            'end_time': datetime.time(12, 0),
            'max_capacity': 6,
            'is_active': True,
        }
    )

    # Find next valid non-Wednesday date
    today = timezone.localdate()
    test_date = today + datetime.timedelta(days=10)
    if test_date.weekday() == 2:
        test_date += datetime.timedelta(days=1)

    # Clear previous audit bookings for this slot & date
    Booking.objects.filter(booking_date=test_date, slot=slot).delete()

    print(f"\nTesting 4 simultaneous threads attempting to book 2 seats each.")
    print(f"Slot capacity = 6. Total requested across 4 threads = 8.")
    print(f"Expected outcome: Exactly 3 succeed (6 pax), exactly 1 fails with capacity error.\n")

    results = {'success': [], 'failed': []}
    lock = threading.Lock()

    def attempt_booking(thread_id):
        # Allow thread-level database connection in Django
        try:
            booking = create_booking_atomic(
                full_name=f"Concurrent Passenger {thread_id}",
                mobile_number=f"987654321{thread_id}",
                email=f"pax{thread_id}@example.com",
                place="Audit Verification",
                booking_date=test_date,
                slot_id=slot.id,
                number_of_members=2
            )
            with lock:
                results['success'].append((thread_id, booking.booking_reference))
                print(f"[Thread {thread_id}] SUCCESS -> Reserved Reference: {booking.booking_reference}")
        except ValidationError as e:
            with lock:
                results['failed'].append((thread_id, str(e)))
                print(f"[Thread {thread_id}] REJECTED -> {e}")
        except Exception as e:
            with lock:
                results['failed'].append((thread_id, str(e)))
                print(f"[Thread {thread_id}] ERROR -> {e}")
        finally:
            connection.close()

    threads = [threading.Thread(target=attempt_booking, args=(i,)) for i in range(1, 5)]
    start_barrier = threading.Barrier(4)

    def synchronized_worker(thread_id):
        start_barrier.wait() # Releases all 4 threads at the exact same microsecond
        attempt_booking(thread_id)

    sync_threads = [threading.Thread(target=synchronized_worker, args=(i,)) for i in range(1, 5)]
    for t in sync_threads:
        t.start()
    for t in sync_threads:
        t.join()

    # Verify final database state
    confirmed_bookings = Booking.objects.filter(
        booking_date=test_date,
        slot=slot,
        status=Booking.Status.CONFIRMED
    )
    total_confirmed_pax = sum(b.number_of_members for b in confirmed_bookings)

    print(f"\n---------------- AUDIT RESULTS ----------------")
    print(f"Total Successful Reservations: {len(results['success'])}")
    print(f"Total Rejected Reservations:   {len(results['failed'])}")
    print(f"Total Confirmed Riders in DB:  {total_confirmed_pax} / {slot.max_capacity}")
    print(f"Overbooking Detected:          {'YES - CRITICAL DEFECT' if total_confirmed_pax > slot.max_capacity else 'NO - CAPACITY PROTECTED'}")
    print(f"------------------------------------------------")

    # Clean up test records
    confirmed_bookings.delete()
    slot.delete()

    assert total_confirmed_pax == 6, f"Expected 6 confirmed pax, got {total_confirmed_pax}"
    assert len(results['success']) == 3, f"Expected 3 successful bookings, got {len(results['success'])}"
    assert len(results['failed']) == 1, f"Expected 1 rejected booking, got {len(results['failed'])}"
    print("ALL INVARIANTS SATISFIED ON MYSQL INNODB.\n")

if __name__ == '__main__':
    run_mysql_audit()
