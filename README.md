# Link & Learn

A peer-to-peer learning platform with a credit-based economy, enabling users to teach and learn from each other.

## Features

- 🎓 **Skill Sharing** - Users can offer and request help with various skills
- 💰 **Credit System** - Earn credits by teaching, spend credits to learn
- 💬 **Real-time Chat** - WebSocket-powered messaging between users
- 📹 **Video Sessions** - Live video calls for teaching sessions
- 🎨 **Collaborative Whiteboard** - Draw and explain concepts together
- 💻 **Integrated IDE** - Code together in real-time

## Tech Stack

- **Backend**: Django 4.2+ with Django Channels
- **WebSockets**: Daphne ASGI server
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: Django Templates with JavaScript

## Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd link_and_learn
   ```

2. **Create virtual environment**
   ```bash
   python -m venv myvenv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows
   myvenv\Scripts\activate
   
   # Linux/Mac
   source myvenv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - Main site: http://127.0.0.1:8000
   - Admin panel: http://127.0.0.1:8000/admin

## Project Structure

```
link_and_learn/
├── chat/               # Real-time chat & WebSocket consumers
├── link_and_learn/     # Main Django project settings
├── requests_app/       # Learning request management
├── skills/             # Skills catalog
├── static/             # Static files (CSS, JS, images)
├── templates/          # HTML templates
├── users/              # User authentication & profiles
├── manage.py           # Django management script
└── requirements.txt    # Python dependencies
```

## Configuration

Key settings in `link_and_learn/settings.py`:

| Setting | Description | Default |
|---------|-------------|---------|
| `INITIAL_USER_CREDITS` | Credits given to new users | 15 |
| `CREDITS_PER_5_MINUTES` | Credits charged per 5 min session | 1 |
| `BANK_CUT_PERCENTAGE` | Platform fee percentage | 10% |
| `SUPPORT_CREDIT_COOLDOWN_HOURS` | Cooldown for support credits | 24h |

## License

This project is for educational purposes.
