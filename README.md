# Delivery Service

[![CI](https://github.com/Iskanderrus/delivery_service/actions/workflows/ci.yml/badge.svg)](https://github.com/Iskanderrus/delivery_service/actions/workflows/ci.yml)

A Django REST backend for a delivery marketplace: customers place orders, shops fulfil them, and drivers deliver — with real road-distance pricing and asynchronous task processing.

## Features

- **Role-based accounts** — custom user model with Customer, Shop, and Driver profiles; JWT authentication (SimpleJWT)
- **Orders with geo-aware pricing** — pickup/drop-off geocoding and road-distance calculation via the OpenRouteService API
- **Async processing** — Celery workers over a Redis broker handle order lifecycle events and driver assignment (per-app signals and tasks)
- **Server-rendered management views** — Django templates with partials for user and product management, alongside the REST API
- **Fully containerised** — Docker Compose stack: Django, PostgreSQL, Redis, pgAdmin

## Architecture

```
                ┌────────────┐
  REST (JWT)    │   Django   │       ┌──────────────────┐
 ────────────►  │  DRF API   │ ────► │ OpenRouteService │
                └─────┬──────┘       │    geocoding +   │
                      │ signals      │    routing API   │
                ┌─────▼──────┐       └──────────────────┘
                │   Celery   │
                │  workers   │
                └─┬────────┬─┘
          ┌───────▼──┐  ┌──▼───────┐
          │  Redis   │  │ Postgres │
          │ (broker) │  │   (DB)   │
          └──────────┘  └──────────┘
```

Domain apps: `accounts` · `products` · `orders` · `delivery`

## Stack

Python 3.12 · Django 5.1 · Django REST Framework · SimpleJWT · Celery · Redis · PostgreSQL · OpenRouteService · Docker Compose

## Running locally

Requires Docker and a `.env` file with PostgreSQL credentials, a Django secret key, and an OpenRouteService API key:

```bash
docker compose up --build
```

The API is served at http://localhost:8000, pgAdmin at http://localhost:8082.

> **Note:** `delivery_service/settings.py` is currently kept out of version control; an env-driven settings module is on the roadmap so the project runs out of the box.

## Tests

Integration-style test suite in `tests/` covering accounts, orders (with mocked routing calls), and delivery flows:

```bash
docker compose exec django python manage.py test tests
```

## License

[MIT](LICENSE)
