# Oasis Chat - Real-Time Multi-Room Chat Application

A premium, modern, real-time multi-room messaging web application built with Python, Flask-SocketIO, and SQLite.

## Features

- **Real-Time Bidirectional Messaging**: Multi-user messaging using Socket.IO (WebSockets).
- **User Authentication**: Secure user registration and login stored in SQLite.
- **Persistent Message History**: Loads past messages when a user joins a room.
- **Multiple Rooms**: Create and join named chat rooms dynamically.
- **Visual Design**: Sleek slate/indigo glassmorphic dashboard interface with responsive layout.
- **Typing Indicator**: Real-time notifications when a user is actively typing.
- **Emoji Support**: Native emoji picker popover and on-the-fly rendering of common shortcodes (e.g., `:smile:`, `:heart:`, `:fire:`).
- **Desktop notifications**: Utilizes HTML5 Notification API with localized audio effects.

---

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Clone or Navigate to the Directory
Navigate to the task folder:
```bash
cd OIBSIP/Python-Task2-ChatApplication
```

### Step 2: Install Dependencies
Install the required packages using pip:
```bash
pip install -r requirements.txt
```

### Step 3: Run the Server
Launch the Flask development server:
```bash
python app.py
```

By default, the server will run on `http://127.0.0.1:5000/`.

### Step 4: Open in Web Browser
Open your favorite web browser and navigate to:
```
http://127.0.0.1:5000/
```

To test real-time functionality, open a second browser window (or incognito tab), create a new account, join the same room, and chat!

---

## Security Transparency & Encryption Awareness

This section provides transparency on how data is handled and security limitations:

### 1. Message Storage
- **How it works**: Chat messages, room metadata, and user associations are stored in an SQLite database file named `chat.db` inside the project folder.
- **Encryption Status**: Messages are stored in **plain text** in the database. Anyone with access to the `chat.db` file can read all chat logs.
- **Recommendation**: In a production environment, the database should be hosted on a secured server, and column-level encryption or database file-level encryption (like SQLCipher) should be applied if messages contain sensitive data.

### 2. User Credentials
- **How it works**: Password authentication is verified on the server.
- **Encryption Status**: Passwords are **not** stored in cleartext. They are hashed using `PBKDF2` with a `SHA256` salt (via `werkzeug.security`).
- **Recommendation**: Hashing is robust and prevents attackers from easily obtaining clear text passwords if the database is leaked.

### 3. Network Transport (Localhost vs Production)
- **How it works**: Web browsers connect to the Flask server via HTTP (for assets/API) and WebSockets (for messaging).
- **Encryption Status**: On `http://localhost`, traffic is transmitted in the clear. Network packets can be captured and read by any agent on the local network (e.g., via Wireshark).
- **Recommendation**: To deploy this application publicly, you must set up an SSL/TLS certificate (HTTPS/WSS) using a reverse proxy (e.g., Nginx, Caddy, or Cloudflare). This ensures all traffic is encrypted in transit between clients and the server.

### 4. End-to-End Encryption (E2EE)
- **How it works**: This application is a standard centralized chat. Messages are decrypted and processed by the server before being saved to the database.
- **Encryption Status**: **No End-to-End Encryption (E2EE)** is implemented. The server operator has full visibility of the conversations.
- **Recommendation**: For true privacy, client-side encryption (using Web Crypto API or similar keys generated in browser) would need to encrypt message payloads *before* they are sent via WebSockets.
