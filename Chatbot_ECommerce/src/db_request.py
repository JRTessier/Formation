import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "orders.db"


# Requete sur une commande
def get_order_by_id(order_id: int, user_id: int) -> dict | None:
    conn = sqlite3.connect(DB_PATH) # ouvre la connexion au fichier .db
    conn.row_factory = sqlite3.Row # configure cette connexion pour obtenir un dictionnaire en sortie
    cursor = conn.execute("SELECT * FROM orders WHERE order_id = ? AND user_id = ?", (order_id, user_id),) # excute la requete sur cette connexion
    ligne = cursor.fetchone()
    conn.close()
    return dict(ligne) if ligne else None

# Tranduction des infos de la commande en langage naturel
# status, date_purchase, date_shipped, date_delivered

STATUS_LABELS = {
    "invoiced": "validée et payée. Elle n'est pas encore expédiée.",
    "shipped": "expédiée et en cours de livraison.",
    "delivered": "livrée."
}

def format_date(raw_date: str) -> str:
    date = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S")
    return date.strftime("%d/%m/%Y")

def format_order_status(order: dict) -> str:
    status_label = STATUS_LABELS.get(order["status"], order["status"]) # Affiche le status au format brut par défaut si besoin
    # status
    lines = [f"Votre commande n°{order["order_id"]} est actuellement {status_label}"]
    # date_purchase
    lines.append(f"Elle a été passée le {format_date(order["date_purchase"])}.")
    # date_shipped
    if order["date_shipped"]:
        lines.append(f"Commande expédiée le {format_date(order["date_shipped"])}.")
    # date_delivered
    if order["date_delivered"]:
            lines.append(f"Livrée le {format_date(order["date_delivered"])}.")

    return " ".join(lines)