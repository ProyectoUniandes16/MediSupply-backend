#!/usr/bin/env python3
"""Script para ejecutar el worker de importación basado en Redis"""

if __name__ == '__main__':
    from app.workers.sqs_worker import run_worker
    run_worker()
