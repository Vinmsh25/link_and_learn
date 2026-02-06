import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'link_and_learn.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Bank, CreditTransaction, Session
from requests_app.models import LearningRequest

User = get_user_model()

def verify():
    print("--- Starting Verification ---")
    
    # 1. Create Users
    print("\n1. Creating Users...")
    try:
        user1 = User.objects.create_user(email='test1@example.com', name='Test User 1', password='password123')
        user2 = User.objects.create_user(email='test2@example.com', name='Test User 2', password='password123')
        print(f"User 1: {user1.name}, Credits: {user1.credits}")
        print(f"User 2: {user2.name}, Credits: {user2.credits}")
        
        assert user1.credits == Decimal('15.00'), "User 1 should have 15 initial credits"
        assert user2.credits == Decimal('15.00'), "User 2 should have 15 initial credits"
        print("✅ User creation and initial credits verified.")
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        return

    # 2. Bank Instance
    print("\n2. Checking Bank...")
    bank = Bank.get_instance()
    print(f"Bank Credits: {bank.total_credits}")
    assert bank.id == 1, "Bank ID should be 1"
    print("✅ Bank instance verified.")

    # 3. Learning Request
    print("\n3. Creating Learning Request...")
    req = LearningRequest.objects.create(
        creator=user1,
        topic_to_learn="Django",
        topic_to_teach="Python"
    )
    print(f"Request: {req.topic_to_learn} by {req.creator.name}")
    print("✅ Learning request created.")

    # 4. Session Logic - Simulation
    print("\n4. Simulating Session & Credits...")
    session = Session.objects.create(user1=user1, user2=user2)
    # Simulate teaching: User 2 teaches User 1 for 10 minutes (2 credits)
    # Bank cut 10% -> 0.2 credits
    # User 2 earns 1.8 credits, User 1 pays 2.0 credits, Bank gets 0.2
    
    # Note: We can't easily simulate time passing for SessionTimer without mocking, 
    # but we can test the session end logic if we could manipulate timer records.
    # Instead, let's manually test bank transaction logic which drives this.
    
    amount = Decimal('2.00')
    bank_cut = amount * Decimal('0.10')
    net_amount = amount - bank_cut
    
    # User 1 pays 2.00
    CreditTransaction.record_transaction(user1, -amount, 'LEARNING')
    # User 2 earns 1.80
    CreditTransaction.record_transaction(user2, net_amount, 'TEACHING')
    # Bank gets 0.20
    bank.add_credits(bank_cut)
    
    user1.refresh_from_db()
    user2.refresh_from_db()
    bank.refresh_from_db()
    
    print(f"User 1 Credits: {user1.credits} (Expected ~13.00)")
    print(f"User 2 Credits: {user2.credits} (Expected ~16.80)")
    print(f"Bank Credits: {bank.total_credits} (Expected +0.20)")
    
    assert user1.credits == Decimal('13.00'), "User 1 should have spent 2.00"
    assert user2.credits == Decimal('16.80'), "User 2 should have earned 1.80"
    print("✅ Credit transactions verified.")

    # 5. Clean up
    print("\n5. Cleaning up...")
    user1.delete()
    user2.delete()
    # Bank persists but that's fine for dev
    print("✅ Cleanup complete.")
    
    print("\n--- Verification Successful ---")

if __name__ == "__main__":
    verify()
