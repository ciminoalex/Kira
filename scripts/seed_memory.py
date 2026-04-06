"""
Pre-popola la memoria di Kira con fatti noti su Alessandro.
Da eseguire una volta al primo setup.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Aggiungi root del progetto al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.config import settings
from agent.memory.supermemory_wrapper import SupermemoryManager

INITIAL_FACTS = [
    # Lavoro
    "Alessandro è Development Manager (Responsabile Sviluppo) presso MTF S.r.l., parte di HTDI Group",
    "MTF ha sedi a Roma, Milano e Vasto. Alessandro è basato a Vasto",
    "Alessandro gestisce un team di sviluppo e implementazioni SAP Business One",
    "Stack tecnico principale: SAP B1 (SQL Server + HANA), C#/.NET, Python, SAP UI5",
    # Clienti attivi
    "Nuova CoGea (NCO): progetto SAP B1 con Go-Live previsto 4 maggio 2026. Alessandro è project lead",
    "ADOTTA Italia: Alessandro è IT Coordinator/SAP Partner Consultant con disponibilità giornaliera",
    "DigitalValue: cliente con 7 schemi SAP, ha avuto un incidente infrastrutturale recente",
    "Essebicarta, Caseificio Di Pasquo, Tailorsan: altri clienti SAP attivi",
    # Progetti
    "AX.360: piattaforma SaaS multi-tenant per task management con AI integrata",
    "D365/Digitale 365: portale project management, in fase commerciale con prospect TMC S.r.l.",
    # Collaboratori chiave
    "Luca Fiscante (LFI): membro del team, coinvolto nel progetto NCO",
    "Mario Prina (MPR): membro del team, coinvolto nel progetto NCO",
    "Marco Casadei (MCA): membro del team, coinvolto nel progetto NCO",
    "Francesca Ruscica: consulente Eulab Consulting per documentazione R&D tax credit",
    "Jacopo Zannier: referente ADOTTA Italia per reportistica e fatturazione",
    # Personale
    "Alessandro è basato nell'area di Vasto, Italia",
    "Ha interesse per lo studio religioso e preparazione discorsi per assemblee",
    "Studia all'Università Telematica Pegaso (Storia della Filologia della Letteratura Italiana)",
    "Preferisce comunicare in italiano, ma gestisce corrispondenza professionale anche in inglese",
]


async def seed_memory() -> None:
    manager = SupermemoryManager(
        api_key=settings.SUPERMEMORY_API_KEY,
        container_tag=settings.SUPERMEMORY_CONTAINER_TAG,
    )

    print(f"Seeding memoria in container '{settings.SUPERMEMORY_CONTAINER_TAG}'...")
    print()

    for fact in INITIAL_FACTS:
        await manager.remember(fact, metadata={"source": "seed", "type": "fact"})
        print(f"  + {fact[:70]}...")

    print(f"\nMemoria inizializzata con {len(INITIAL_FACTS)} fatti.")
    print(f"Container: {settings.SUPERMEMORY_CONTAINER_TAG}")


if __name__ == "__main__":
    asyncio.run(seed_memory())
