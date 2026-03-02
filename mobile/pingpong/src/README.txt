╔══════════════════════════════════════════════════════════════╗
║                   CTF Challenge: PingPong                    ║
║              Category: Misc  |  Difficulty: Medium           ║
╚══════════════════════════════════════════════════════════════╝

DESCRIPTION
───────────
A suspicious Android application called PingPong has been
intercepted. It appears to communicate with a remote server,
but all credentials and endpoints are hidden inside the app.

Your goal is to reverse engineer the application, uncover the
hidden secrets, and exploit the backend API to retrieve the
flag.

SERVER
──────
The backend server is running and waiting for you.
Connect to:

    Host : <SERVER_IP>
    Port : 8080

All API calls should be made to:

    http://<SERVER_IP>:8080

FILES
─────
  PingPong.apk   →  The Android application to reverse engineer

OBJECTIVE
─────────
Retrieve the flag.

    Flag format:  CHC{...}

Good luck.
