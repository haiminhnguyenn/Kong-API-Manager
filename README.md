# 🌐 Flask Backend for Kong Gateway Management
> A Flask-based backend service is designed to facilitate the interaction between clients and Kong Gateway

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.0.1-green)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.8.16-orange)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13-blue)
![Kong Gateway](https://img.shields.io/badge/Kong%20Gateway-2.x-blueviolet)

## 📖 Description

This is a Flask backend that serves as an intermediary between the client and Kong Gateway. The goal of the project is to provide a user-friendly interface that simplifies CRUD (Create, Read, Update, Delete) operations related to services, routes, and plugins on Kong Gateway, hiding the complex processing logic from the end user.

## 🌟 Features

- **⚡ Asynchronous Task Handling:** Uses RabbitMQ to handle tasks like creating, updating, and deleting APIs asynchronously, improving performance and responsiveness.
- **💾 Data Persistence:** Stores responses from Kong Gateway in PostgreSQL to efficiently serve subsequent GET requests from the client.
- **🔧 Simplified API Management:** Provides an interface for users to manage services, routes, and plugins without needing to interact directly with Kong Gateway, reducing the complexity of operations.
- **🔌 Plugin Management:** Allows users to manage plugins for specific APIs, enabling or disabling them based on the corresponding routes mapped to APIs on Kong Gateway.

## 🗄️ Database Structure

This project uses PostgreSQL to store API and Plugin configurations and task results. Below is the database diagram that illustrates the relationships between the tables:
![Database Diagram](https://github.com/user-attachments/assets/ff374bc2-a217-4c29-b955-c2e67b487e54)

## 🎯 Benefits

- **👌 User-Friendly Interface:** Simplifies the interaction with Kong Gateway, making it easier for users to manage their APIs without deep knowledge of Kong’s internal workings.
- **🚀 Performance Optimization:** Asynchronous processing via RabbitMQ ensures that tasks are handled efficiently without blocking the main application flow.
- **🛡️ Data Integrity:** All changes and configurations are stored in PostgreSQL, providing a reliable way to track and retrieve API configurations.
- **📈 Scalability:** The use of asynchronous processing and separate database storage allows the system to scale effectively as the number of APIs grows.

## ⚙️ Getting Started

To get started with the application, follow these steps:

### 🚀 Prerequisites

Setting up:

* Install 🦍 **[Kong Gateway](https://docs.konghq.com/gateway/latest/install)**.
* Install database 🐘 **[PosgreSQL](https://www.postgresql.org/download/)** to store configuration details.
* Install task queue 🐇 **[RabbitMQ](https://www.rabbitmq.com/docs/download)** to handle asynchronous tasks.

### 🛠️ Installation

1. Clone the repo
```sh
git clone https://github.com/haiminhnguyenn/Kong-API-Manager.git
```
2. Create a virtualenv and install the requirements, use [PyPI](https://pypi.org) by running the following command:
```sh
pip install -r requirements.txt
```
3. Open a second terminal window and start a Celery worker:
```sh
celery -A celery_worker.celery worker --loglevel=info
```
4. Start Kong API Management on your first terminal window:
```sh
python3 run.py
```

## 📋 Usage

- To manage APIs (services, routes, plugins), send requests to the appropriate endpoints. The backend will handle the interactions with Kong Gateway and RabbitMQ.
- Use the provided GET endpoints to retrieve the current configuration and status of your APIs from the PostgreSQL database.
