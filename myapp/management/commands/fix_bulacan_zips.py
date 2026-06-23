
import requests
from django.core.management.base import BaseCommand

from ...models import PostalCode  # adjust relative import depth if needed
from ...data.zip_codes import BULACAN_ZIPS  # ← the data now lives here

PSGC_BASE = "https://psgc.cloud/api"


def clean_name(raw):
    """Same double-encoding fix used in the pds.html JS, mirrored here."""
    if not raw:
        return ""
    s = raw.strip()
    if "Ã" in s:
        try:
            s = s.encode("latin1").decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass
    return s


def to_display_name(name):
    if name.startswith("City of "):
        return name[len("City of "):]
    if name.startswith("Municipality of "):
        return name[len("Municipality of "):]
    return name


class Command(BaseCommand):
    help = "Fix/seed correct PHLPost ZIP codes for all Bulacan cities/municipalities."

    def handle(self, *args, **options):
        # 1. Find Bulacan's province code so we can scope the city search to it
        provinces = requests.get(f"{PSGC_BASE}/provinces", timeout=10).json()
        bulacan = next(
            (p for p in provinces if clean_name(p["name"]).lower() == "bulacan"),
            None,
        )
        if not bulacan:
            self.stderr.write(self.style.ERROR("Could not find Bulacan in psgc.cloud /provinces"))
            return
        prov_prefix = bulacan["code"][:5]

        # 2. Pull all cities + municipalities, keep only Bulacan's
        cities = requests.get(f"{PSGC_BASE}/cities", timeout=10).json()
        munis = requests.get(f"{PSGC_BASE}/municipalities", timeout=10).json()
        bulacan_places = [
            c for c in (cities + munis) if c["code"][:5] == prov_prefix
        ]

        fixed, missing = [], []

        for town_name, correct_zip in BULACAN_ZIPS.items():
            match = None
            for place in bulacan_places:
                name = clean_name(place["name"])
                display = to_display_name(name)
                if town_name.lower() in (name.lower(), display.lower()):
                    match = place
                    break

            if not match:
                missing.append(town_name)
                continue

            PostalCode.objects.update_or_create(
                psgc_city_code=match["code"],
                defaults={
                    "city_name": town_name,
                    "province_name": "Bulacan",
                    "zip_code": correct_zip,
                },
            )
            fixed.append(f"{town_name} ({match['code']}) -> {correct_zip}")

        for line in fixed:
            self.stdout.write(self.style.SUCCESS(f"Fixed: {line}"))
        for town_name in missing:
            self.stdout.write(self.style.WARNING(f"Could not match in psgc.cloud: {town_name}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Fixed {len(fixed)} of {len(BULACAN_ZIPS)} Bulacan towns."
        ))