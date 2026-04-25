# 🐾 PawsHaven — Vulnerable Veterinary & Animal Rescue Platform

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Flask Version](https://img.shields.io/badge/flask-3.1.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

PawsHaven is an intentionally vulnerable web application designed for security professionals, students, and CTF enthusiasts to practice penetration testing and vulnerability research. It simulates a modern Veterinary & Animal Rescue platform with a wide array of security flaws ranging from simple misconfigurations to critical remote code execution.

> [!CAUTION]
> **WARNING:** This application is **intentionally vulnerable** and contains severe security flaws. **DO NOT** deploy this application to any production server or expose it to the internet. Use it only in a strictly controlled, isolated lab environment.

---

## 🚀 Features

- **Animal Management:** Browse, search, and import animal records (XML/JSON).
- **Community Portal:** User registration, profiles, stray reporting, and commenting system.
- **Premium Membership:** Exclusive "Galaxy Live" interactive theme and advanced diagnostic tools.
- **E-commerce Store:** Supplies shop with coupon codes and invoice generation.
- **Admin Dashboard:** Centralized management for users, appointments, and system integrations.

---

## 🛠️ Technology Stack

- **Backend:** Python 3.x with Flask
- **Frontend:** Jinja2 Templates, Vanilla CSS/JS
- **Database:** SQLite3 (isolated per-user sandboxes)
- **Authentication:** JWT (JSON Web Tokens) with various intentional implementation flaws
- **Internal Services:** Simulated microservices for SSRF and integration testing

---

## 🚩 Security Lab: Vulnerabilities

PawsHaven contains over **33 documented vulnerabilities** (and potentially more) across several categories:

- **Injection:** Command Injection, SQL Injection, SSTI (Server-Side Template Injection), XXE.
- **Broken Access Control:** IDOR (Insecure Direct Object Reference), BOLA, Method Tampering.
- **Authentication:** JWT Secret Forgery, `alg: none` bypass, Weak Password Policies, 2FA bypass.
- **Cross-Site Scripting (XSS):** Stored, Reflected, and Blind XSS across multiple vectors.
- **Server-Side Request Forgery (SSRF):** Internal service enumeration and blacklist bypass.
- **File Security:** LFI (Local File Inclusion), Path Traversal, Unrestricted File Uploads.
- **Business Logic:** Coupon reuse, Race Conditions, Price Manipulation.

For a detailed list and reproduction steps, refer to:
- [`docs/Vulnerability_Assessment_Report.md`](docs/Vulnerability_Assessment_Report.md)
- [`docs/CTF_Solutions.md`](docs/CTF_Solutions.md)

---

## 🔧 Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/your-repo/PawsHaven.git
   cd PawsHaven
   ```

2. **Install Dependencies:**
   It is recommended to use a virtual environment.
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the Application:**
   ```bash
   python app.py
   ```
   The application will be accessible at `http://localhost:5000`.


---

## 🧪 Documentation

Detailed documentation is available in the `docs/` directory:
- **[API Specification (JSON)](docs/API.json)**
- **[API Specification (YAML)](docs/api.yaml)**
- **[Vulnerability Assessment Report](docs/Vulnerability_Assessment_Report.md)**
- **[CTF Solutions Manual](docs/CTF_Solutions.md)**

---

## 🤝 Contributing

This project is built for educational purposes. If you find a new vulnerability or want to improve the existing labs, feel free to submit a pull request!

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

**Happy Hacking!** 🐾
