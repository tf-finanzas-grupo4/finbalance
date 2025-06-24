# FinBalance

Sistema de gestión financiera personal desarrollado con Django.

## Requisitos Previos

- Python 3.13 o superior
- pip (administrador de paquetes de Python)
- Git (para clonar el repositorio)

## Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/finbalance.git
cd finbalance
```

### 2. Crear y Activar el Entorno Virtual

#### En macOS/Linux:
```bash
python3 -m venv finbalance_env
source finbalance_env/bin/activate
```

#### En Windows:
```bash
python -m venv finbalance_env
finbalance_env\Scripts\activate
```

### 3. Instalar Dependencias
```bash
pip install django
# Añadir otras dependencias si son necesarias
```

## Uso

### Activar el Entorno Virtual

Cada vez que trabajes en el proyecto, necesitas activar el entorno virtual:

#### En macOS/Linux:
```bash
source finbalance_env/bin/activate
```

#### En Windows:
```bash
finbalance_env\Scripts\activate
```

Sabrás que el entorno está activado cuando veas `(finbalance_env)` al inicio de la línea de comandos.

### Desactivar el Entorno Virtual

Cuando termines de trabajar en el proyecto, puedes desactivar el entorno virtual:

```bash
deactivate
```

### Ejecutar el Servidor de Desarrollo

```bash
python manage.py runserver
```

El servidor estará disponible en [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Comandos Útiles de Django

### Crear Migraciones
```bash
python manage.py makemigrations
```

### Aplicar Migraciones
```bash
python manage.py migrate
```

### Crear Superusuario
```bash
python manage.py createsuperuser
```

### Entrar al Shell de Django
```bash
python manage.py shell
```

## Estructura del Proyecto

(Aquí puedes describir la estructura de tu proyecto cuando esté más avanzado)

## Contribuir

(Instrucciones para contribuir al proyecto)

## Licencia

(Información sobre la licencia del proyecto)