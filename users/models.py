"""
User models for Link & Learn.
Includes custom User, Bank, CreditTransaction, Session, SessionTimer, and Review.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        if 'credits' not in extra_fields:
            user.credits = Decimal(str(settings.INITIAL_USER_CREDITS))
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with email authentication and credits."""
    
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)
    name = models.CharField(max_length=150)
    credits = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('15.00'),
        help_text='User credit balance'
    )
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    availability = models.CharField(max_length=255, blank=True, default='')
    last_support_request = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return self.name
    
    @property
    def average_rating(self):
        reviews = self.reviews_received.all()
        if not reviews.exists():
            return None
        return reviews.aggregate(models.Avg('rating'))['rating__avg']
    
    @property
    def total_reviews(self):
        return self.reviews_received.count()
    
    @property
    def total_sessions(self):
        return Session.objects.filter(
            models.Q(user1=self) | models.Q(user2=self),
            end_time__isnull=False
        ).count()


class Bank(models.Model):
    """
    Singleton Bank that accumulates 10% cut from teaching credits.
    Provides support to low-credit users.
    """
    
    total_credits = models.DecimalField(
        max_digits=15, decimal_places=2,
        default=Decimal('100.00'),
        help_text='Total credits in bank'
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'bank'
    
    def __str__(self):
        return f"Bank ({self.total_credits} credits)"
    
    @classmethod
    def get_instance(cls):
        bank, _ = cls.objects.get_or_create(pk=1)
        return bank
    
    def add_credits(self, amount):
        self.total_credits += Decimal(str(amount))
        self.save(update_fields=['total_credits', 'updated_at'])
    
    def deduct_credits(self, amount):
        self.total_credits -= Decimal(str(amount))
        self.save(update_fields=['total_credits', 'updated_at'])
    
    def get_support_amount(self, user_credits):
        """Calculate support amount based on user's current credits."""
        credits = float(user_credits)
        if credits <= 0:
            return 6
        elif credits <= 2:
            return 4
        elif credits <= 3:
            return 2
        return 0


class CreditTransaction(models.Model):
    """Tracks all credit movements for audit trail."""
    
    TRANSACTION_TYPES = [
        ('TEACHING', 'Teaching Earned'),
        ('LEARNING', 'Learning Spent'),
        ('SIGNUP', 'Signup Bonus'),
        ('SUPPORT', 'Bank Support'),
        ('BANK_CUT', 'Bank Cut'),
        ('DONATION', 'Donation'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='credit_transactions'
    )
    session = models.ForeignKey(
        'Session', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='credit_transactions'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.name}: {self.amount:+.2f} ({self.transaction_type})"
    
    @classmethod
    def record_transaction(cls, user, amount, transaction_type, session=None, description=''):
        from django.db import transaction as db_transaction
        with db_transaction.atomic():
            user.credits += Decimal(str(amount))
            user.save(update_fields=['credits'])
            return cls.objects.create(
                user=user,
                session=session,
                amount=Decimal(str(amount)),
                transaction_type=transaction_type,
                balance_after=user.credits,
                description=description
            )


class Session(models.Model):
    """Learning session between two users."""
    
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessions_as_user1'
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessions_as_user2'
    )
    learning_request = models.ForeignKey(
        'requests_app.LearningRequest',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sessions'
    )
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # State Persistence
    whiteboard_state = models.TextField(blank=True, default='')
    ide_code = models.TextField(blank=True, default='// Start coding...')
    ide_language = models.CharField(max_length=50, default='javascript')
    
    class Meta:
        ordering = ['-start_time']
    
    def __str__(self):
        return f"Session: {self.user1.name} <-> {self.user2.name}"
    
    @property
    def total_duration(self):
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (timezone.now() - self.start_time).total_seconds()
    
    def get_teaching_time(self, user):
        total_seconds = 0
        for timer in self.timers.filter(teacher=user):
            total_seconds += timer.duration_seconds
        return total_seconds
    
    def end_session(self):
        self.is_active = False
        self.end_time = timezone.now()
        for timer in self.timers.filter(end_time__isnull=True):
            timer.stop()
        self.save(update_fields=['is_active', 'end_time'])
    
    def get_active_timer(self):
        return self.timers.filter(end_time__isnull=True).first()
    
    def calculate_credits(self):
        """Calculate credits for both users based on teaching time."""
        from django.conf import settings as conf
        
        user1_teaching_seconds = self.get_teaching_time(self.user1)
        user2_teaching_seconds = self.get_teaching_time(self.user2)
        
        # 5 minutes = 1 credit
        user1_earned = (user1_teaching_seconds // 300) * conf.CREDITS_PER_5_MINUTES
        user2_earned = (user2_teaching_seconds // 300) * conf.CREDITS_PER_5_MINUTES
        
        # Bank cut is 10%
        user1_net = user1_earned * (1 - conf.BANK_CUT_PERCENTAGE / 100)
        user2_net = user2_earned * (1 - conf.BANK_CUT_PERCENTAGE / 100)
        
        bank_cut = (user1_earned + user2_earned) * conf.BANK_CUT_PERCENTAGE / 100
        
        return {
            'user1_earned': user1_net,
            'user2_earned': user2_net,
            'user1_spent': user2_earned,  # user1 pays for user2's teaching
            'user2_spent': user1_earned,  # user2 pays for user1's teaching
            'bank_cut': bank_cut
        }


class SessionTimer(models.Model):
    """Per-user teaching timer within a session."""
    
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='timers')
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teaching_timers'
    )
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-start_time']
    
    def __str__(self):
        return f"Timer: {self.teacher.name} in session {self.session.id}"
    
    @property
    def is_running(self):
        return self.end_time is None
    
    def stop(self):
        if self.end_time is None:
            self.end_time = timezone.now()
            self.duration_seconds = int((self.end_time - self.start_time).total_seconds())
            self.save(update_fields=['end_time', 'duration_seconds'])
    
    @classmethod
    def start_timer(cls, session, teacher):
        running_timer = session.get_active_timer()
        if running_timer:
            running_timer.stop()
        return cls.objects.create(session=session, teacher=teacher, start_time=timezone.now())


class Review(models.Model):
    """Session review/rating."""
    
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given'
    )
    reviewee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_received'
    )
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['session', 'reviewer']
    
    def __str__(self):
        return f"{self.reviewer.name} -> {self.reviewee.name} ({self.rating}/5)"
