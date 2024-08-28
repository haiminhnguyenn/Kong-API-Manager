# 🌐 Flask Backend for Kong Gateway Management
> A Flask-based backend service is designed to facilitate the interaction between clients and Kong Gateway

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.0.1-green)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.8.16-orange)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13-blue)
![Kong Gateway](https://img.shields.io/badge/Kong%20Gateway-2.x-blueviolet)

## 🚀 Description

This is a Flask-based backend application designed to manage Kong Gateway configurations. It provides CRUD operations for services, routes, and plugins on the Kong Gateway. The backend leverages RabbitMQ as a task queue to handle asynchronous requests, ensuring efficient processing of create, update, and delete actions. PostgreSQL is used as the database to store configuration details, allowing for quick retrieval of information when users request it. This architecture ensures optimal performance, scalability, and seamless integration with Kong Gateway, providing a robust solution for managing API gateway configurations.


## ⚙️ Getting Started

To get started with the application, follow these steps:

### Prerequisites

Setting up:

* Install 🦍 **[Kong Gateway](https://docs.konghq.com/gateway/latest/install)**.
* Install database 🐘 **[PosgreSQL](https://www.postgresql.org/download/)** to store configuration details.
* Install task queue 🐇 **[RabbitMQ](https://www.rabbitmq.com/docs/download)** to handle asynchronous tasks.

### Installation

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