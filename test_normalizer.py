from normalizers.vehicle_normalizer import VehicleNormalizer


def main():

    normalizer = VehicleNormalizer()

    test_titles = [
        "BYD ATTO 2 1.5 PHEV BOOST AT",
        "BYD SEALION 7 82.5 KWH DESIGN AWD",
        "OPEL CORSA 1.2 TURBO 100HP EDITION",
        "OPEL COMBO CARGO 1.5 DÍZEL (75 KW/100 LE)",
        "PEUGEOT 408 HYBRID 145 E-DCT6 ALLURE 5D",
        "KIA PV5 Long Range DCT 163 HP",
    ]

    for title in test_titles:

        result = normalizer.normalize(title)

        print("\nOriginal:", result["original_title"])
        print("Brand:", result["brand"])
        print("Model:", result["model"])
        print("Fuel:", result["fuel_type"])


if __name__ == "__main__":
    main()