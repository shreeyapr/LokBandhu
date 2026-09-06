# 🇮🇳 LokBandhu

### Bridging Citizens and Government : One Click at a Time

**LokBandhu** is a multilingual digital public-service platform designed to simplify communication between citizens and government services. The platform provides citizens with a centralized interface to submit and track complaints, discover categorized public services, interact with an AI-powered chatbot, and receive email notifications.

The system provides separate **Citizen** and **Administrator** modules with role-based access control for secure management of complaints, users, and services.

---

## 📌 Project Overview

LokBandhu — meaning **"Friend of the People"** — aims to make public-service access simpler, more accessible, and more user-friendly through a centralized digital platform.

### Core capabilities

* 📝 Citizen complaint registration and tracking
* 🏛️ Categorized government/public-service directory
* 🤖 LokSeva AI chatbot
* 🌐 Multilingual user interface
* 📧 Automated Gmail email notifications
* 👤 Citizen and Administrator modules
* 🔐 Role-based access control
* 📊 Administrator dashboard and management tools
* 📱 Responsive interface using Bootstrap

The platform supports **six languages**:

* English
* Hindi
* Marathi
* Bengali
* Tamil
* Telugu

---

## ✨ Features

### 👤 Citizen Module

Citizens can:

* Register and log in securely
* Submit public-service complaints
* Select complaint categories
* Provide complaint details and address information
* Attach supporting images/PDF files
* Receive a unique complaint ID
* Track complaint status
* Browse categorized government services
* Interact with the LokSeva chatbot
* Use the interface in multiple Indian languages

### 🛡️ Administrator Module

Administrators can:

* Access the administrative dashboard
* Manage registered users
* Manage citizen complaints
* Update complaint status
* Manage public-service records
* Perform CRUD operations on services
* Monitor platform information through dashboard views

### 🤖 LokSeva AI Chatbot

LokSeva provides an AI-assisted conversational interface for helping users find relevant information and navigate public-service functionality.

The chatbot uses:

* Natural Language Processing
* NLTK
* Scikit-learn
* A trained chatbot model
* Intent-based responses

### 🌐 Multilingual Support

LokBandhu provides a multilingual interface supporting:

**English | Hindi | Marathi | Bengali | Tamil | Telugu**

Language detection and language-specific routing are handled through the application's language utilities and routes.

### 📧 Email Notifications

The system includes automated email notifications using **Gmail SMTP**, allowing users to receive updates related to complaint processing and other system activities.

---

## 🏗️ System Architecture

LokBandhu follows an MVC-oriented Flask architecture with modular Flask Blueprints.

```text
                         ┌─────────────────────┐
                         │       User          │
                         │  Citizen / Admin    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Flask Application │
                         │       (app.py)      │
                         └──────────┬──────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             ▼                      ▼                      ▼
      ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
      │ Auth Routes │       │Citizen/Admin│       │ Chat Routes │
      │             │       │   Routes    │       │  LokSeva AI │
      └─────────────┘       └─────────────┘       └─────────────┘
             │                      │                      │
             └──────────────────────┼──────────────────────┘
                                    ▼
                         ┌─────────────────────┐
                         │    SQLAlchemy ORM   │
                         └──────────┬──────────┘
                                    ▼
                         ┌─────────────────────┐
                         │ SQLite / MySQL      │
                         └─────────────────────┘
```

### Application structure

```text
LokBandhu/
│
├── app.py
├── config.py
├── extensions.py
├── requirements.txt
│
├── chatbot_model.pkl
├── intents.json
├── train_advanced.py
│
├── database/
│   └── init_db.py
│
├── models/
│   ├── __init__.py
│   └── db_models.py
│
├── routes/
│   ├── __init__.py
│   ├── admin_routes.py
│   ├── auth_routes.py
│   ├── chat_routes.py
│   ├── citizen_routes.py
│   └── lang_routes.py
│
├── utils/
│   ├── __init__.py
│   ├── email_service.py
│   ├── lang_detector.py
│   └── translations.py
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── images/
│   └── uploads/
│
└── templates/
    ├── admin/
    ├── auth/
    ├── citizen/
    ├── about.html
    ├── contact.html
    ├── index.html
    ├── layout.html
    └── services_landing.html
```

---

## 🛠️ Technology Stack

| Category               | Technology                   |
| ---------------------- | ---------------------------- |
| Backend                | Python, Flask 3.x            |
| ORM                    | Flask-SQLAlchemy             |
| Authentication         | Flask-Login                  |
| Security               | Werkzeug                     |
| Frontend               | HTML5, CSS3, Bootstrap 5.3.3 |
| Database – Development | SQLite 3.x                   |
| Database – Production  | MySQL 8.x                    |
| Chatbot                | NLTK, Scikit-learn           |
| Language Detection     | Langdetect                   |
| Charts                 | Chart.js                     |
| Icons                  | Font Awesome                 |
| Typography             | Google Noto Sans             |
| Email                  | Gmail SMTP                   |
| Version Control        | Git & GitHub                 |

---

## 🔐 Security

LokBandhu implements several application-level security mechanisms:

* Password hashing using Werkzeug
* PBKDF2-SHA256 password hashing
* Flask-Login session management
* Role-based access control
* Protected administrator routes
* Environment-based secret configuration
* Local database stored inside Flask's `instance` directory

Sensitive environment configuration should be supplied through environment variables rather than committed to the repository.

---

## 🗃️ Data Model

The application uses relational data models for:

### Users

Stores user account and role information.

### Complaints

Stores citizen complaints, associated information, and complaint status.

Supported complaint statuses include:

```text
Submitted
In Progress
Resolved
Closed
```

### Services

Stores categorized public-service information.

Service categories include:

```text
Rural
Urban
Metro
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/shreeyapr/LokBandhu.git
cd LokBandhu
```

### 2. Create a virtual environment

#### Windows

```cmd
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Set a secure Flask secret key through your environment.

#### Windows CMD

```cmd
set SECRET_KEY=your-secure-secret-key
```

#### PowerShell

```powershell
$env:SECRET_KEY="your-secure-secret-key"
```

For persistent or production configuration, use an appropriate environment configuration system.

### 5. Initialize the database

```bash
python database/init_db.py
```

### 6. Run the application

```bash
python app.py
```

The Flask development server will start locally.

---

## 🧪 Testing

The project report documents **24 test cases** covering areas including:

* Authentication
* Complaint management
* Service directory
* Multilingual functionality
* Chatbot functionality

The reported test execution recorded all 24 test cases as passed.

---

## 🔮 Future Enhancements

Planned/future improvements described for the project include:

* SMS notifications
* Advanced search and filtering
* Pagination
* Password reset
* Mobile application
* Geolocation-based services
* Complaint assignment
* OTP-based verification
* Citizen feedback/rating
* Government API integration
* Predictive analytics
* Offline/PWA capabilities
* Multi-tenancy support

---

## 🎯 Project Objectives

The project focuses on:

1. Providing a centralized public-service platform.
2. Simplifying citizen complaint registration and tracking.
3. Improving accessibility through multilingual support.
4. Providing categorized government-service information.
5. Providing AI-assisted citizen interaction through LokSeva.
6. Providing administrators with tools to manage users, complaints, and services.
7. Supporting secure role-based access to application functionality.

---


## 📚 Academic Project

**Programme:** Master of Computer Applications (MCA)
**Semester:** II
**Academic Year:** 2025–2026

---

## 📄 Project Documentation

The detailed academic project report is maintained separately from the source repository.

---

## 📜 License

This project was developed as an academic project. A formal open-source license can be added if the project is intended for public reuse or distribution.

---

## ⭐ Acknowledgement

LokBandhu was developed as an academic project with the objective of exploring full-stack web development, database management, multilingual interfaces, NLP-based chatbot functionality, authentication, and digital public-service platforms.

> **LokBandhu — Bridging Citizens and Government, One Click at a Time.**
