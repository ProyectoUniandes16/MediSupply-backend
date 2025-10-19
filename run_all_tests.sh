#!/bin/bash

set -e

# Tabla de comandos y cobertura mínima
SERVICES=(
  "productos_microservice|pytest tests/ --cov=app.models --cov=app.services.csv_service --cov=app.services.producto_service --cov=app.utils --cov-report=xml --cov-fail-under=70"
  "vendedores_microservice|pytest test/unit/ --cov=app --cov-report=xml --cov-fail-under=80"
  "mediador-web|pytest --cov=. --cov-report=xml --cov-fail-under=80"
  "auth-usuario|pytest --cov=. --cov-report=xml --cov-fail-under=80"
  "proveedores_microservice|pytest --cov=. --cov-report=xml --cov-fail-under=80"
  "producto-inventario-web|pytest --cov=. --cov-report=xml --cov-fail-under=80"
)

printf "\n================= RESULTADOS DE TESTS Y COBERTURA =================\n"
for entry in "${SERVICES[@]}"; do
  IFS='|' read -r folder cmd <<< "$entry"
    echo "\n--- $folder ---"
    pushd "$folder" > /dev/null
    if [ -f requirements.txt ]; then
      echo "Instalando dependencias en $folder..."
      pip install -r requirements.txt
    fi
    eval $cmd | tee -a ../test_results.log
    popd > /dev/null
done
printf "\n==============================================================\n"
