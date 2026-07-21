# Guía de comandos Git usados

Este archivo documenta los comandos utilizados para preparar y publicar el repositorio en GitHub.

## Comandos usados para crear la conexión y conectarte a GitHub

```bash
git remote add origin https://github.com/miguelquesadamartinez/drone-env.git

git config --global user.name "Miguel Quesada"
git config --global user.email "miguel.quesada.martinez.1975@gmail.com"

ssh -T git@github.com
```

## 1. Verificar estado del repositorio

```bash
git status --short --branch
git branch -a
git remote -v
git rev-parse --show-toplevel
```

## 2. Crear y configurar un archivo .gitignore

```bash
printf '%s
' 'bin/' 'include/' 'lib/' 'lib64/' '.venv/' '.env' 'pyvenv.cfg' '__pycache__/' '*.pyc' '*.pyo' '.pytest_cache/' '.mypy_cache/' '.idea/' '.vscode/' > .gitignore
```

## 3. Añadir archivos al área de staging

```bash
git add .gitignore

git add README.md despegar.py deteccion_personas_ai.py detectar_personas.py \
mision.py movimiento.py prueba_camara.py seguir_persona.py telemetria.py
```

## 4. Crear el primer commit

```bash
git commit -m "Primer commit del proyecto"
```

## 5. Renombrar la rama a main

```bash
git branch -M main
```

## 6. Publicar en GitHub

```bash
git push -u origin main
```

## 7. Verificar el último commit

```bash
git log --oneline -1
git status --short --branch
```

## 8. Comprobar si un archivo está siendo ignorado

```bash
git check-ignore -v lib64
```

## Notas

- El error inicial ocurrió porque el repositorio no tenía commits aún y Git intentaba hacer push de una rama que todavía no existía.
- El comando `git branch -M main` renombró la rama actual a `main`.
- El archivo `.gitignore` evita subir carpetas y archivos generados por el entorno virtual y Python.
