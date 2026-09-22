"""
Generador de dataset sintetico para simulacion de flujo de pacientes
en urgencias de un hospital (Hospital Emergency Room Patient Flow).

Ejecucion:
    python src/generator.py
"""

import csv
import os
import random
from datetime import datetime, timedelta

# ------------------------------------------------------------------
# Configuracion general
# ------------------------------------------------------------------

TOTAL_RECORDS = 100_000
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "emergency_patients.csv")
LOG_EVERY = 10_000

FIELDNAMES = [
    "stream_seq",
    "patient_id",
    "arrival_time",
    "triage_level",
    "chief_complaint",
    "department",
    "wait_time_min",
    "current_occupancy",
    "is_admitted",
]
DUPLICATE_RATE = 0.07  # ~7% de patient_id reutilizados (rango pedido: 6%-8%)
PERIOD_DAYS = 30

CHIEF_COMPLAINTS = [
    "Dolor toracico",
    "Dificultad respiratoria",
    "Fiebre alta",
    "Trauma en extremidad",
    "Cefalea severa",
    "Dolor abdominal",
    "Convulsiones",
    "Reaccion alergica",
    "Laceracion profunda",
    "Perdida de conciencia",
]

DEPARTMENTS = [
    "Trauma",
    "Pediatria",
    "Cardiologia",
    "Urgencias Generales",
    "Ortopedia",
    "Neurologia",
]

# Pesos desiguales para forzar distribucion sesgada (util para AMS Sketch / F2)
DEPARTMENT_WEIGHTS = [15, 15, 15, 40, 10, 5]

TRIAGE_LEVELS = [1, 2, 3, 4, 5]
TRIAGE_WEIGHTS = [5, 10, 35, 35, 15]

random.seed(42)


def generate_patient_id(counter: int) -> str:
    return f"PAT-{counter:05d}"


def build_record(stream_seq: int, arrival_time: datetime, seen_ids: list) -> tuple:
    """Construye un registro y retorna (record, patient_id_generado_o_None)."""

    reuse = seen_ids and random.random() < DUPLICATE_RATE
    if reuse:
        patient_id = random.choice(seen_ids)
        new_id = None
    else:
        new_counter = 10000 + stream_seq
        patient_id = f"PAT-{new_counter}"
        new_id = patient_id

    triage_level = random.choices(TRIAGE_LEVELS, weights=TRIAGE_WEIGHTS, k=1)[0]

    chief_complaint = random.choice(CHIEF_COMPLAINTS)

    department = random.choices(DEPARTMENTS, weights=DEPARTMENT_WEIGHTS, k=1)[0]

    if triage_level <= 2:
        wait_time_min = round(random.uniform(0.0, 15.0), 1)
    else:
        wait_time_min = round(random.uniform(20.0, 180.0), 1)

    current_occupancy = random.randint(5, 60)

    if triage_level <= 2:
        is_admitted = random.random() < 0.85
    else:
        is_admitted = random.random() < 0.20

    record = {
        "stream_seq": stream_seq,
        "patient_id": patient_id,
        "arrival_time": arrival_time.isoformat(),
        "triage_level": triage_level,
        "chief_complaint": chief_complaint,
        "department": department,
        "wait_time_min": wait_time_min,
        "current_occupancy": current_occupancy,
        "is_admitted": is_admitted,
    }

    return record, new_id


def generate_dataset() -> None:
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    start_time = datetime(2026, 1, 1, 0, 0, 0)
    # Incremento promedio para cubrir PERIOD_DAYS con TOTAL_RECORDS registros
    total_seconds = PERIOD_DAYS * 24 * 60 * 60
    avg_increment = total_seconds / TOTAL_RECORDS

    current_time = start_time
    seen_ids = []

    print(f"Generando {TOTAL_RECORDS:,} registros sinteticos...")

    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for stream_seq in range(1, TOTAL_RECORDS + 1):
            increment = random.uniform(avg_increment * 0.3, avg_increment * 1.7)
            current_time += timedelta(seconds=increment)

            record, new_id = build_record(stream_seq, current_time, seen_ids)
            if new_id is not None:
                seen_ids.append(new_id)

            writer.writerow(record)

            if stream_seq % LOG_EVERY == 0:
                print(f"  -> {stream_seq:,} / {TOTAL_RECORDS:,} registros generados")

    print("Generacion completada.")


def validate_output() -> None:
    if not os.path.exists(OUTPUT_PATH):
        raise FileNotFoundError(f"No se encontro el archivo de salida en {OUTPUT_PATH}")

    size_bytes = os.path.getsize(OUTPUT_PATH)
    size_mb = size_bytes / (1024 * 1024)

    with open(OUTPUT_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        row_count = sum(1 for _ in reader) - 1  # descuenta encabezado

    assert row_count == TOTAL_RECORDS, f"Se esperaban {TOTAL_RECORDS} registros, se encontraron {row_count}"

    print(f"Archivo validado correctamente: {OUTPUT_PATH}")
    print(f"Registros: {row_count:,}")
    print(f"Tamano del archivo: {size_mb:.2f} MB")


if __name__ == "__main__":
    generate_dataset()
    validate_output()
