# TechCafe-Backend

## Table of Contents

- [TechCafe Backend](#TechCafe-Backend)
  - [Introduction](#introduction)
  - [Features](#features)
  - [Getting Started](#getting-started)
    - [Installation](#installation)
  - [Database schema](#database-schema)
  - [License](#license)

## Introduction

This the backend source code of tech cafe website. used django rest framework and postgres database 

## Features

- Django LTS
- Custom User Model
- Signal attachments
- Django RestFramework
- JWT Authentication
- APi Docs
- Bank Gateway
- Discount model
- Checkin System for users

## Getting Started

To get this repository, run the following command inside your terminal
```shell
git clone https://github.com/H-VICTOOR/TechCafe-Backend.git
```

### Installation

Before proceeding with the installation, make sure to perform the following steps:

1. **Edit Environment Files:**

   - Navigate to the following paths within your project directory:

     ```shell
     envs/prod/db/.env.sample
     envs/prod/django/.env.sample
     ```

   - Rename these `.env.sample` files to `.env`.

   - Open each `.env` file and configure your environment variables as needed for your project.

2. **Edit Nginx Configuration:**

   - Locate the `default.conf` file in the root directory of your project.

   - Open the `default.conf` file and customize the Nginx configuration settings according to your project requirements.

3. **Docker Setupn:**

If you want to run the project locally, make sure you have Docker installed. You can download it from Docker's official website.

4. **Running the Project:**

To run the project in a production environment and deploy it on a VPS, use the following command:

```shell
docker-compose-prod up -d
```
To run the project for development purposes, use the following command:

```shell
docker-compose up -d
```
These commands will start the necessary Docker containers and run your project. Make sure to replace docker-compose-prod with the actual name of your production Docker Compose file if it's different.

After starting the Docker container, follow these commands to set up your database and create a superuser:


**Migrate Database:**

   Run the following commands to apply database migrations:

   ```shell
   docker exec -it backend sh -c "python manage.py makemigrations accounts"
   docker exec -it backend sh -c "python manage.py makemigrations gathering"
   docker exec -it backend sh -c "python manage.py migrate"
```
**create Super User:**
```
docker exec -it backend sh -c "python manage.py createsuperuser"
```

## Database schema
<p align="center">
<img src="https://github.com/H-VICTOOR/TechCafe-Backend/blob/main/demo/database_schema.png" alt="database schema" width="300"/>
</p>

## license
MIT license
