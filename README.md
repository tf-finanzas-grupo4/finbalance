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

## Run Tailwindcss
```bash
cd finbalance
python manage.py tailwind start
```

## Run Project
```bash
cd finbalance
python manage.py runserver
```

## Base de Datos y Configuración

### Estructura de la Base de Datos

El proyecto utiliza SQLite como base de datos. La tabla principal `bonds_bond` incluye los siguientes campos:

#### Campos del Modelo Bond:
- `valor_nominal` - Valor nominal del bono (DecimalField)
- `valor_comercial` - Valor comercial del bono (DecimalField)
- `num_anios` - Número de años del bono (IntegerField)
- `frecuencia_cupon` - Frecuencia del cupón (IntegerField con choices)
- `dias_por_anio` - Días por año (IntegerField: 360 o 365)
- `tipo_tasa_interes` - Tipo de tasa de interés (CharField: nominal/efectiva)
- `capitalizacion` - Frecuencia de capitalización (IntegerField, opcional)
- `tasa_interes` - Tasa de interés en porcentaje (DecimalField)
- `tasa_anual_descuento` - Tasa anual de descuento (DecimalField)
- `impuesto_renta` - Impuesto a la renta (DecimalField)
- `fecha_emision` - Fecha de emisión (DateField)
- `porcentaje_prima` - Porcentaje de prima (DecimalField)
- `tipo_prima` - Tipo de prima (CharField)
- `porcentaje_estructuracion` - Porcentaje de estructuración (DecimalField)
- `tipo_estructuracion` - Tipo de estructuración (CharField)
- `porcentaje_colocacion` - Porcentaje de colocación (DecimalField)
- `tipo_colocacion` - Tipo de colocación (CharField)
- `porcentaje_flotacion` - Porcentaje de flotación (DecimalField)
- `tipo_flotacion` - Tipo de flotación (CharField)
- `porcentaje_cavali` - Porcentaje CAVALI (DecimalField)
- `tipo_cavali` - Tipo CAVALI (CharField)
- `metodo_amortizacion` - Método de amortización (CharField)
- `fecha_registro` - Fecha de registro automática (DateTimeField)

### Administración

#### Acceder al Admin de Django
```bash
# URL: http://127.0.0.1:8000/admin/
# Usuario: admin
# Contraseña: admin123
```

#### Crear Superusuario (si es necesario)
```bash
python manage.py createsuperuser
```

### Migrar la Base de Datos

Si necesitas recrear la base de datos:

```bash
# Eliminar base de datos actual (¡cuidado, elimina todos los datos!)
rm db.sqlite3

# Crear nuevas migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser
```

### Verificar Estructura de la Tabla

Para verificar la estructura de la tabla `bonds_bond`:

```bash
sqlite3 db.sqlite3 "PRAGMA table_info(bonds_bond);"
```

### Visualizar Base de Datos

#### Opción 1: Extensión VS Code
- Instalar extensión "SQLite Viewer" o "Database Client"
- Hacer clic derecho en `db.sqlite3` → "Open Database"

#### Opción 2: DB Browser for SQLite (Herramienta Externa)
```bash
# Instalar con Homebrew (macOS)
brew install --cask db-browser-for-sqlite

# Abrir base de datos
open -a "DB Browser for SQLite" db.sqlite3
```

#### Opción 3: Terminal
```bash
# Abrir SQLite en terminal
sqlite3 db.sqlite3

# Comandos útiles:
.tables          # Ver todas las tablas
.schema          # Ver esquema completo
SELECT * FROM bonds_bond LIMIT 10;  # Ver datos de bonos
.quit            # Salir
```