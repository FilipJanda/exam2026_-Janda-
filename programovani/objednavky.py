import argparse
import csv
from pathlib import Path

TRUE_VALUES = {"true"}
FALSE_VALUES = {"false"}


def parse_bool(value):
    if value is None:
        return None
    value = str(value).strip().lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    return None


def parse_int(value):
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None


def parse_float(value):
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return None


def load_orders(path, orders=None):
    if orders is None:
        orders = {}

    with open(path, encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            order_id = row.get("cislo_objednavky")
            if order_id is None:
                continue
            order_id = str(order_id).strip()
            if not order_id:
                continue

            zakaznik = str(row.get("zakaznik", "")).strip()
            zaplaceno = parse_bool(row.get("zaplaceno"))
            nazev_polozky = str(row.get("nazev_polozky", "")).strip()
            mnozstvi = parse_int(row.get("mnozstvi"))
            cena_za_kus = parse_float(row.get("cena_za_kus"))

            order = orders.setdefault(
                order_id,
                {
                    "cislo_objednavky": order_id,
                    "zakaznik": zakaznik,
                    "zaplaceno": zaplaceno,
                    "items": [],
                },
            )

            if order["zakaznik"] == "" and zakaznik:
                order["zakaznik"] = zakaznik

            if zaplaceno is False:
                order["zaplaceno"] = False
            elif zaplaceno is True and order["zaplaceno"] is None:
                order["zaplaceno"] = True

            if not is_valid_item(nazev_polozky, mnozstvi, cena_za_kus):
                continue

            order["items"].append(
                {
                    "nazev_polozky": nazev_polozky,
                    "mnozstvi": mnozstvi,
                    "cena_za_kus": cena_za_kus,
                }
            )

    return orders


def is_valid_item(name, quantity, price):
    if not name:
        return False
    if quantity is None or quantity <= 0:
        return False
    if price is None or price <= 0:
        return False
    return True


def build_valid_orders(orders):
    valid_orders = []
    for order in orders.values():
        if order.get("zaplaceno") is not True:
            continue
        if not order.get("items"):
            continue

        total = 0.0
        item_count = 0
        for item in order["items"]:
            total += item["mnozstvi"] * item["cena_za_kus"]
            item_count += item["mnozstvi"]

        if item_count <= 0:
            continue

        valid_orders.append(
            {
                "cislo_objednavky": order["cislo_objednavky"],
                "zakaznik": order["zakaznik"],
                "zaplaceno": order["zaplaceno"],
                "items": order["items"],
                "celkem": total,
                "pocet_polozek": item_count,
            }
        )
    return valid_orders


def sort_orders(orders):
    def order_key(order):
        try:
            cislo = int(order["cislo_objednavky"])
        except ValueError:
            cislo = order["cislo_objednavky"]
        return (-order["celkem"], -order["pocet_polozek"], cislo)

    return sorted(orders, key=order_key)


def print_orders(orders):
    for order in orders:
        print(
            f"Objednávka {order['cislo_objednavky']} | zákazník: {order['zakaznik']} | "
            f"celkem: {order['celkem']:.2f} | počet položek: {order['pocet_polozek']}"
        )
        print()


def resolve_input_path(file_name):
    path = Path(file_name)
    if path.exists():
        return path

    script_dir = Path(__file__).resolve().parent
    alt_path = script_dir / file_name
    if alt_path.exists():
        return alt_path

    return path


def main():
    parser = argparse.ArgumentParser(description="Zpracování objednávek ze souborů CSV.")
    parser.add_argument(
        "files",
        nargs="*",
        default=["simple.csv", "complex.csv"],
        help="Cesty k CSV souborům (výchozí: simple.csv complex.csv)",
    )
    args = parser.parse_args()

    orders = {}
    for file_name in args.files:
        path = resolve_input_path(file_name)
        if not path.exists():
            raise SystemExit(f"Soubor nenalezen: {path}")
        load_orders(path, orders)

    valid_orders = build_valid_orders(orders)
    sorted_orders = sort_orders(valid_orders)
    print_orders(sorted_orders)


if __name__ == "__main__":
    main()
