# 🦍 Flask Backend for Kong API Management

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.0.1-green)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.8.16-orange)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13-blue)
![Kong Gateway](https://img.shields.io/badge/Kong%20Gateway-2.x-blueviolet)

🚀 **Simplify your Kong Gateway Management** with this Flask Backend. This project serves as a middleware between clients and the Kong Gateway, providing a user-friendly interface for managing services, routes, and plugins, while hiding complex logic and ensuring data integrity.

## 🎯 Features

- **CRUD Operations**: Perform create, read, update, and delete operations on Kong services, routes, and plugins.
- **Request Validation**: Validates requests from clients before forwarding them to Kong to ensure data consistency and correctness.
- **Asynchronous Rollbacks**: Utilizes RabbitMQ to rollback changes asynchronously in case of errors during Kong operations, ensuring smooth user experience.
- **Persistent Storage**: Saves API and Plugin data into a PostgreSQL database after successful requests to Kong. This allows you to retrieve the information quickly from the database for GET requests.
- **Error Handling**: When requests fail, return clear and informative error messages to the client.

## 🛠️ Tech Stack

- **Flask**: Lightweight Python web framework for building the API.
- **Kong Gateway**: Powerful API gateway used for managing services, routes, and plugins.
- **PostgreSQL**: Database for persisting API and Plugin information.
- **RabbitMQ**: Message broker for asynchronous task handling and rollbacks.
- **WSL Ubuntu**: Running environment on Windows Subsystem for Linux.

## 🚧 How It Works

1. **Validation**: The backend validates incoming client requests for CRUD operations. If the request is valid, it proceeds to Kong Gateway; otherwise, an error is returned.
2. **Kong Interaction**: The backend sends valid requests to Kong Gateway to manage services, routes, and plugins.
3. **Data Persistence**: After receiving a successful response from Kong, the data is saved into PostgreSQL for later retrieval.
4. **Error Management**: If something goes wrong during interaction with Kong, RabbitMQ is triggered to rollback any recent changes asynchronously.

## 🗄️ Database Structure

This project uses PostgreSQL to store API and Plugin configurations and task results. Below is the database diagram that illustrates the relationships between the tables:
![Database Diagram](https://github.com/user-attachments/assets/ff374bc2-a217-4c29-b955-c2e67b487e54)

## 🌟 Benefits

- **Simplified User Interaction**: Users no longer need to handle the complexity of Kong's API directly. The backend provides a straightforward interface for managing services, routes, and plugins.
- **Data Consistency**: By validating client requests before they reach Kong, the backend ensures that only accurate and compatible data is sent, minimizing errors.
- **Reduced Downtime**: With RabbitMQ handling rollbacks asynchronously, you can easily revert changes without impacting the client experience or causing service disruptions.
- **Faster Access to Data**: Storing API and Plugin data in PostgreSQL ensures quicker access when handling GET requests, rather than repeatedly querying Kong.
- **Error Transparency**: Clear and concise error messages help users understand what went wrong without having to dig through complex error logs from Kong.

## ⚙️ Installation

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