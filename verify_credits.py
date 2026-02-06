import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'link_and_learn.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Session, SessionTimer, Bank, CreditTransaction

User = get_user_model()

import sys

def verify_credits():
    sys.stderr.write("Starting verification...\n")
    with open('verify_log.txt', 'w') as f:
        sys.stdout = f
        print("--- Verifying Credit Logic ---")
    
    # 1. Setup Users
    u1, _ = User.objects.get_or_create(email='u1@test.com', defaults={'name': 'User One', 'credits': Decimal('20.00')})
    u2, _ = User.objects.get_or_create(email='u2@test.com', defaults={'name': 'User Two', 'credits': Decimal('20.00')})
    
    # Reset credits
    u1.credits = Decimal('20.00')
    u2.credits = Decimal('20.00')
    u1.save()
    u2.save()
    
    bank = Bank.get_instance()
    bank_initial = bank.total_credits
    
    print(f"Initial: U1={u1.credits}, U2={u2.credits}, Bank={bank_initial}")

    # 2. Create Session
    session = Session.objects.create(user1=u1, user2=u2)
    
    # 3. Simulate Teaching: User 2 teaches User 1 for 10 minutes (2 credits)
    # 10 mins = 600 seconds
    timer = SessionTimer.objects.create(
        session=session,
        teacher=u2,
        duration_seconds=600
    )
    # We must set end_time to make it "stopped" if logic checks that, 
    # but get_teaching_time sums duration_seconds.
    
    # 4. End Session & Calculate
    print("Ending session...")
    # mimic the view logic
    session.end_session() 
    credits = session.calculate_credits()
    
    print(f"Calculated Credits: {credits}")
    
    # Check Math before applying
    # User 2 taught 10 mins. 5 mins = 1 credit. Total = 2 credits.
    # U2 eans 2 * 0.9 = 1.8.
    # U1 spends 2.
    # Bank gets 2 * 0.1 = 0.2.
    
    expected_u2_earned = 1.8
    expected_u1_spent = 2.0
    expected_bank_cut = 0.2
    
    if float(credits['user2_earned']) != expected_u2_earned:
        print(f"FAIL: Expected U2 earned {expected_u2_earned}, got {credits['user2_earned']}")
    else:
        print("PASS: U2 Earned calculation correct.")
        
    if float(credits['user1_spent']) != expected_u1_spent:
        print(f"FAIL: Expected U1 spent {expected_u1_spent}, got {credits['user1_spent']}")
    else:
        print("PASS: U1 Spent calculation correct.")

    if float(credits['bank_cut']) != expected_bank_cut:
        print(f"FAIL: Expected Bank cut {expected_bank_cut}, got {credits['bank_cut']}")
    else:
        print("PASS: Bank Cut calculation correct.")
        
    # 5. Apply transactions (mimicking view logic manually to inspect)
    # Real logic is in views.py end_session. We should probably use the view or mimic it exactly.
    # Let's mimic exactly what views.py does:
    
    # U2 Earns
    if credits['user2_earned'] > 0:
        CreditTransaction.record_transaction(
            user=session.user2,
            amount=credits['user2_earned'],
            transaction_type='TEACHING',
            session=session
        )
    
    # U1 Spends
    if credits['user1_spent'] > 0:
        CreditTransaction.record_transaction(
            user=session.user1,
            amount=-credits['user1_spent'], # Negative for spent
            transaction_type='LEARNING',
            session=session
        )
        
    # Bank Cut
    if credits['bank_cut'] > 0:
        bank.add_credits(credits['bank_cut'])
        
    # 6. Verify Final State
    u1.refresh_from_db()
    u2.refresh_from_db()
    bank.refresh_from_db()
    
    print(f"Final: U1={u1.credits}, U2={u2.credits}, Bank={bank.total_credits}")
    
    if u1.credits != Decimal('18.00'): # 20 - 2
        print(f"FAIL: U1 balance incorrect. Expected 18.00, got {u1.credits}")
    else:
        print("PASS: U1 Balance correct.")
        
    if u2.credits != Decimal('21.80'): # 20 + 1.8
        print(f"FAIL: U2 balance incorrect. Expected 21.80, got {u2.credits}")
    else:
        print("PASS: U2 Balance correct.")
        
    expected_bank = bank_initial + Decimal('0.20')
    if bank.total_credits != expected_bank:
        print(f"FAIL: Bank balance incorrect. Expected {expected_bank}, got {bank.total_credits}")
    else:
        print("PASS: Bank Balance correct.")

if __name__ == '__main__':
    try:
        verify_credits()
    except Exception as e:
        sys.stderr.write(f"ERROR: {e}\n")
        import traceback
        traceback.print_exc(file=sys.stderr)
