from pathlib import Path

ARVAL = Path("scrapers/arval/acquisition_connector.py")
AYVENS = Path("scrapers/ayvens/acquisition_connector.py")


ARVAL_CONTEXT_OLD = """        current_duration = getattr(
            task,
            "current_duration",
            None,
        )
        current_mileage = getattr(
            task,
            "current_mileage",
            None,
        )
"""

ARVAL_CONTEXT_NEW = ARVAL_CONTEXT_OLD + """        target_duration = getattr(
            task,
            "target_duration",
            None,
        )
        target_mileage = getattr(
            task,
            "target_mileage",
            None,
        )
"""

AYVENS_CONTEXT_OLD = """        current_duration = getattr(task, "current_duration", None)
        current_mileage = getattr(task, "current_mileage", None)
        current_url = getattr(task, "current_url", None)
"""

AYVENS_CONTEXT_NEW = """        current_duration = getattr(task, "current_duration", None)
        current_mileage = getattr(task, "current_mileage", None)
        target_duration = getattr(task, "target_duration", None)
        target_mileage = getattr(task, "target_mileage", None)
        current_url = getattr(task, "current_url", None)
"""


ARVAL_GUARD_OLD = """                # The evidence must actually resolve a contract gap.
                if (
                    current_duration is not None
                    and current_mileage is not None
                    and offer.duration == current_duration
                    and offer.mileage == current_mileage
                ):
                    continue
"""

AYVENS_GUARD_OLD = """                # Same observed contract dimensions do not resolve a
                # normalization gap even if the URL is different.
                if (
                    current_duration is not None
                    and current_mileage is not None
                    and offer.duration == current_duration
                    and offer.mileage == current_mileage
                ):
                    continue
"""

TARGET_GUARD = """                # Target Contract Discovery V1:
                # accept only the exact endpoint required by this comparison.
                if (
                    target_duration is not None
                    and offer.duration != target_duration
                ):
                    continue

                if (
                    target_mileage is not None
                    and offer.mileage != target_mileage
                ):
                    continue

                # Backward-compatible safety when no explicit target exists.
                if (
                    target_duration is None
                    and target_mileage is None
                    and current_duration is not None
                    and current_mileage is not None
                    and offer.duration == current_duration
                    and offer.mileage == current_mileage
                ):
                    continue
"""


def patch_one(path, context_old, context_new, guard_old):
    original = path.read_text(encoding="utf-8")
    text = original

    # Idempotent context insertion.
    if 'target_duration = getattr' not in text:
        if context_old not in text:
            raise RuntimeError(
                f"{path}: exact contract context block not found"
            )
        text = text.replace(
            context_old,
            context_new,
            1,
        )

    # Idempotent guard replacement.
    if "Target Contract Discovery V1:" not in text:
        if guard_old not in text:
            raise RuntimeError(
                f"{path}: exact old contract guard not found"
            )
        text = text.replace(
            guard_old,
            TARGET_GUARD,
            1,
        )

    # Validate BEFORE writing.
    compile(text, str(path), "exec")

    backup = path.with_suffix(
        path.suffix + ".pre_target_contract_v1_exact"
    )

    if not backup.exists():
        backup.write_text(
            original,
            encoding="utf-8",
        )

    path.write_text(
        text,
        encoding="utf-8",
    )

    print("PATCHED:", path)
    print("BACKUP :", backup)


def main():
    patch_one(
        ARVAL,
        ARVAL_CONTEXT_OLD,
        ARVAL_CONTEXT_NEW,
        ARVAL_GUARD_OLD,
    )

    patch_one(
        AYVENS,
        AYVENS_CONTEXT_OLD,
        AYVENS_CONTEXT_NEW,
        AYVENS_GUARD_OLD,
    )

    print(
        "\nTARGET CONTRACT CONNECTOR PATCH V1 EXACT APPLIED"
    )


if __name__ == "__main__":
    main()
