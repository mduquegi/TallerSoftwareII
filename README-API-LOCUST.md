# API Laravel 9 — Laboratorio Locust

API REST para practicar pruebas de **carga**, **estrés** y **capacidad** con [Locust](https://locust.io/).

## Requisitos

- PHP 8.0+
- Composer
- MySQL o PostgreSQL (recomendado para 1.5M registros)
- Extensión PHP correspondiente (`pdo_mysql` / `pdo_pgsql`)

## Instalación

```bash
cd laravel-api
composer install
cp .env.example .env   # si aplica
php artisan key:generate
```

Configure la base de datos en `.env`:

```env
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=locust_lab
DB_USERNAME=root
DB_PASSWORD=
```

```bash
php artisan migrate:fresh --seed
```

Eso ejecuta `DatabaseSeeder`, que llama a `MassUserSeeder` (1.500.000 usuarios por defecto).

Opcional en `.env`:

```env
MASS_USER_SEED_COUNT=1500000
MASS_USER_CHUNK_SIZE=2000
```

Alternativa sin borrar tablas:

```bash
php artisan users:seed-mass --count=1500000 --chunk=2000
```

El seed masivo puede tardar varios minutos según el hardware. Ajuste `MASS_USER_CHUNK_SIZE` o `--chunk` si hay errores de memoria.

## Endpoints (con paginación)

Base URL: `http://HOST:PUERTO/api`

Los tres GET usan paginación en la base de datos. `per_page` acepta valores entre 1 y 200 y usa 50 por defecto. La consulta de `over-twenty` filtra por `birth_date` antes de paginar, por lo que no carga el millón y medio de filas en memoria.

| Método | Ruta | Comportamiento actual |
|--------|------|------------------------|
| GET | `/users` | Listado paginado (`page`, `per_page`) |
| GET | `/users/emails` | Listado paginado con `id` y `email` |
| GET | `/users/over-twenty` | Filtrado por fecha y listado paginado |
| POST | `/users/bulk` | Crea **exactamente 3** usuarios (sin cambios) |

Archivo a modificar: `app/Http/Controllers/Api/UserController.php`.

### Ejemplos de paginación

```http
GET /api/users?page=2&per_page=50
GET /api/users/emails?per_page=25
GET /api/users/over-twenty?page=1&per_page=100
```

Las respuestas de los dos primeros endpoints conservan el formato estándar de Laravel (`current_page`, `data`, `last_page`, `total`, etc.). `over-twenty` devuelve esos mismos metadatos dentro de `users` y agrega `cutoff_date`.

### Ejemplo GET usuarios

```http
GET /api/users HTTP/1.1
Host: localhost:8000
Accept: application/json
```

Respuesta: objeto paginado con los usuarios de la página solicitada (sin contraseña).

### Ejemplo POST bulk (3 usuarios)

```http
POST /api/users/bulk HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Accept: application/json

{
  "users": [
    {
      "name": "Ana López",
      "email": "ana.locust@example.com",
      "birth_date": "1998-05-12"
    },
    {
      "name": "Bruno Díaz",
      "email": "bruno.locust@example.com",
      "birth_date": "2000-11-03",
      "password": "secreto123"
    },
    {
      "name": "Carla Ruiz",
      "email": "carla.locust@example.com",
      "birth_date": "1995-01-20"
    }
  ]
}
```

Respuesta `201` con los tres usuarios creados (sin contraseña en JSON).

## Factory (datos pequeños)

```bash
php artisan tinker
>>> \App\Models\User::factory(100)->create();
```

La factory genera `birth_date` aleatoria entre 10 y 70 años atrás.

## Servidor de desarrollo

```bash
php artisan serve --host=0.0.0.0 --port=8000
```

Para pruebas de carga reales, use PHP-FPM + Nginx/Apache y OPcache en un entorno dedicado, no el servidor embebido de `artisan serve`.

## Locust

Crear un entorno virtual e instalar las dependencias:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

El archivo `locustfile.py` valida el estado HTTP y la estructura de cada respuesta, genera correos únicos para el POST y mantiene la mezcla 5:3:2:1 entre los tres GET y el alta masiva. Las clases `LoadUser`, `StressUser` y `CapacityUser` permiten separar las ejecuciones:

```bash
locust -f locustfile.py --host=http://127.0.0.1:8000
locust -f locustfile.py --user-classes LoadUser --headless -u 30 -r 3 -t 10m --html=report-load.html
locust -f locustfile.py --user-classes StressUser --headless -u 200 -r 20 -t 10m --html=report-stress.html
locust -f locustfile.py --user-classes CapacityUser --headless -u 50 -r 5 -t 60m --html=report-capacity.html
```

Los valores de usuarios, `spawn rate`, duración, host, versión de Locust y estado de la API deben quedar registrados en el informe junto con p95, RPS y tasa de errores. No se deben presentar resultados de rendimiento sin ejecutar las pruebas en el entorno elegido.
