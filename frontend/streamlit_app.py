import sys
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from comparison.live_comparison_service import (
    DEFAULT_ARVAL_URL,
    DEFAULT_AYVENS_URL,
    LiveComparisonService,
)
from market_intelligence.market_dashboard_service import (
    MarketDashboardService,
)
from market_intelligence.benchmark_dashboard_service import (
    BenchmarkDashboardService,
)


st.set_page_config(
    page_title="Fleet Intelligence",
    page_icon="🚗",
    layout="wide",
)


def huf(value):
    if value is None:
        return "—"
    return f"{value:,.0f} Ft".replace(",", " ")


def status_badge(status):
    mapping = {
        "COMPARABLE": "🟢",
        "MATCH": "🟢",
        "EQUIVALENT": "🟢",
        "READY_FOR_PRICE_COMPARISON": "🟢",
        "INSUFFICIENT_EVIDENCE": "🟠",
        "NEEDS_TERM_NORMALIZATION": "🟠",
        "VALUE_DIFFERENCE": "🟠",
        "DIFFERENCE": "🔴",
        "NOT_COMPARABLE": "🔴",
    }
    return mapping.get(status, "⚪")


def offer_df(offers):
    rows = []

    for offer in offers:
        rows.append(
            {
                "Provider": offer.get("provider"),
                "Brand": offer.get("brand"),
                "Model": offer.get("model"),
                "Trim": offer.get("trim"),
                "Fuel": offer.get("fuel_type"),
                "Monthly Fee": offer.get("monthly_fee"),
                "Duration": offer.get("duration"),
                "Mileage": offer.get("mileage"),
                "Identity": offer.get("identity_status"),
                "Last Seen": offer.get("last_seen_at"),
                "URL": offer.get("url"),
            }
        )

    return pd.DataFrame(rows)


def filtered_offers(data):
    offers = list(data.offers)

    st.subheader("Szűrők")
    f1, f2, f3 = st.columns(3)

    provider = f1.multiselect(
        "Provider",
        data.providers,
    )

    brand = f2.multiselect(
        "Márka",
        data.brands,
    )

    fuel_options = sorted({
        item.get("fuel_type") or "UNKNOWN"
        for item in offers
    })

    fuel = f3.multiselect(
        "Hajtás",
        fuel_options,
    )

    model_options = sorted({
        item.get("model")
        for item in offers
        if item.get("model")
    })

    model = st.multiselect(
        "Modell",
        model_options,
    )

    out = []

    for item in offers:
        if provider and item.get("provider") not in provider:
            continue
        if brand and item.get("brand") not in brand:
            continue
        if model and item.get("model") not in model:
            continue
        if fuel and (item.get("fuel_type") or "UNKNOWN") not in fuel:
            continue
        out.append(item)

    return out


def render_market_overview(data):
    st.header("Market Overview")
    st.caption(
        "Aktuális, deduplikált piaci állapot az egységes market persistence-ből."
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Összes ajánlat", data.offer_count)
    k2.metric("Szolgáltatók", data.provider_count)
    k3.metric("Átlagos havidíj", huf(data.average_monthly_fee_huf))
    k4.metric("Medián havidíj", huf(data.median_monthly_fee_huf))

    offers = filtered_offers(data)
    df = offer_df(offers)

    if df.empty:
        st.warning("Nincs a szűrésnek megfelelő ajánlat.")
        return

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Ajánlatok providerenként")
        chart = (
            df.groupby("Provider")
            .size()
            .rename("Ajánlatok")
        )
        st.bar_chart(chart)

    with c2:
        st.subheader("Átlagos havidíj providerenként")
        chart = (
            df.dropna(subset=["Monthly Fee"])
            .groupby("Provider")["Monthly Fee"]
            .mean()
            .round()
        )
        st.bar_chart(chart)

    st.subheader("Hajtáslánc megoszlás")
    fuel_chart = (
        df.fillna({"Fuel": "UNKNOWN"})
        .groupby("Fuel")
        .size()
        .rename("Ajánlatok")
    )
    st.bar_chart(fuel_chart)

    st.subheader("Aktuális ajánlatok")
    display = df.copy()
    display["Monthly Fee"] = display["Monthly Fee"].map(huf)
    display["Duration"] = display["Duration"].map(
        lambda x: f"{int(x)} hó" if pd.notna(x) else "—"
    )
    display["Mileage"] = display["Mileage"].map(
        lambda x: (
            f"{int(x):,} km/év".replace(",", " ")
            if pd.notna(x)
            else "—"
        )
    )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "URL": st.column_config.LinkColumn(
                "Forrás",
                display_text="Megnyitás",
            ),
        },
    )


def render_provider_comparison(data):
    st.header("Provider Comparison")

    if not data.provider_metrics:
        st.warning("Nincs provider adat.")
        return

    rows = []

    for provider, metrics in data.provider_metrics.items():
        rows.append(
            {
                "Provider": provider,
                "Offers": metrics["offer_count"],
                "Average Fee": metrics["average_monthly_fee_huf"],
                "Median Fee": metrics["median_monthly_fee_huf"],
                "Min Fee": metrics["min_monthly_fee_huf"],
                "Max Fee": metrics["max_monthly_fee_huf"],
            }
        )

    df = pd.DataFrame(rows)

    st.dataframe(
        df.assign(
            **{
                "Average Fee": df["Average Fee"].map(huf),
                "Median Fee": df["Median Fee"].map(huf),
                "Min Fee": df["Min Fee"].map(huf),
                "Max Fee": df["Max Fee"].map(huf),
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Provider median havidíjak")
    st.bar_chart(
        df.set_index("Provider")["Median Fee"]
    )

    st.info(
        "Ez a nézet még nyers piaci árszinteket mutat. "
        "Futamidő, km, önerő, felszereltség és szolgáltatás "
        "normalizálása nélkül nem szabad belőle közvetlen price winner-t levonni."
    )


def render_offer_explorer(data):
    st.header("Vehicle / Offer Explorer")

    offers = filtered_offers(data)
    df = offer_df(offers)

    if df.empty:
        st.warning("Nincs találat.")
        return

    sort_choice = st.selectbox(
        "Rendezés",
        (
            "Havidíj növekvő",
            "Havidíj csökkenő",
            "Márka / modell",
            "Provider",
        ),
    )

    if sort_choice == "Havidíj növekvő":
        df = df.sort_values("Monthly Fee", ascending=True)
    elif sort_choice == "Havidíj csökkenő":
        df = df.sort_values("Monthly Fee", ascending=False)
    elif sort_choice == "Márka / modell":
        df = df.sort_values(["Brand", "Model"], na_position="last")
    else:
        df = df.sort_values(["Provider", "Brand", "Model"], na_position="last")

    st.caption(f"{len(df)} ajánlat")

    display = df.copy()
    display["Monthly Fee"] = display["Monthly Fee"].map(huf)

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "URL": st.column_config.LinkColumn(
                "Forrás",
                display_text="Megnyitás",
            ),
        },
    )


def render_price_history(data):
    st.header("Price History & Changes")

    changes = pd.DataFrame(list(data.changes))

    if changes.empty:
        st.info(
            "Még csak egy market snapshot áll rendelkezésre. "
            "Árváltozás a következő sikeres market run után jelenik meg."
        )
    else:
        changed = changes[
            changes["delta_huf"].notna()
            & (changes["delta_huf"] != 0)
        ].copy()

        if changed.empty:
            st.info(
                "Van történeti adat, de a legutóbbi két megfigyelés között "
                "nem találtunk árváltozást."
            )
        else:
            changed = changed.sort_values(
                "delta_huf"
            )

            st.subheader("Legutóbbi árváltozások")

            display = changed[
                [
                    "provider",
                    "brand",
                    "model",
                    "trim",
                    "previous_fee",
                    "latest_fee",
                    "delta_huf",
                    "delta_percent",
                    "latest_observed_at",
                    "url",
                ]
            ].copy()

            for col in (
                "previous_fee",
                "latest_fee",
                "delta_huf",
            ):
                display[col] = display[col].map(huf)

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "url": st.column_config.LinkColumn(
                        "Forrás",
                        display_text="Megnyitás",
                    ),
                },
            )

    history = pd.DataFrame(list(data.history))

    if history.empty:
        return

    st.subheader("Egy ajánlat ártrendje")

    history["label"] = (
        history["provider"].fillna("")
        + " | "
        + history["brand"].fillna("")
        + " "
        + history["model"].fillna("")
        + " | "
        + history["duration"].astype(str)
        + " hó / "
        + history["mileage"].astype(str)
    )

    selected = st.selectbox(
        "Ajánlat",
        sorted(history["label"].unique()),
    )

    selected_df = history[
        history["label"] == selected
    ].copy()

    selected_df["observed_at"] = pd.to_datetime(
        selected_df["observed_at"],
        errors="coerce",
    )

    selected_df = selected_df.sort_values("observed_at")

    st.line_chart(
        selected_df.set_index("observed_at")["monthly_fee"]
    )



def render_benchmark_intelligence():
    data = load_benchmark_data()

    st.header("Benchmark Intelligence")
    st.caption(
        "A legutóbbi automatikus benchmark batch evidence-first eredményei."
    )

    if data.run is None:
        st.warning(
            "Még nincs lezárt benchmark batch a fleet.db adatbázisban."
        )
        return

    run = data.run

    st.caption(
        f"Benchmark run #{run['id']} · {run['status']} · "
        f"{run.get('completed_at') or run.get('started_at')}"
    )

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Benchmark pairs", data.pair_count)
    k2.metric("Evaluated", data.evaluated_count)
    k3.metric("Failed", data.failed_count)
    k4.metric("Price comparable", data.price_comparable_count)
    k5.metric("Blocked", data.blocked_count)

    st.info(
        "A 'Blocked' itt azt jelenti, hogy a FullComparison nem engedélyezte "
        "a price comparisont. A dashboard ebből nem képez saját árgyőztest."
    )

    if data.blocker_counts:
        st.subheader("Top blockers")
        blocker_df = pd.DataFrame(
            [
                {
                    "Blocker": code,
                    "Pairs": count,
                }
                for code, count in data.blocker_counts.items()
            ]
        ).set_index("Blocker")

        st.bar_chart(blocker_df["Pairs"])

        st.dataframe(
            blocker_df.reset_index(),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("A legutóbbi batchben nincs aktív blocker.")

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Comparison status")
        if data.comparison_status_counts:
            status_df = pd.DataFrame(
                [
                    {
                        "Status": key,
                        "Pairs": value,
                    }
                    for key, value in data.comparison_status_counts.items()
                ]
            ).set_index("Status")
            st.bar_chart(status_df["Pairs"])

    with c2:
        st.subheader("Market pair status")
        if data.pair_status_counts:
            pair_df = pd.DataFrame(
                [
                    {
                        "Status": key,
                        "Pairs": value,
                    }
                    for key, value in data.pair_status_counts.items()
                ]
            ).set_index("Status")
            st.bar_chart(pair_df["Pairs"])

    st.subheader("Benchmark Result Explorer")

    results = list(data.results)

    if not results:
        st.info("A legutóbbi benchmark run nem tartalmaz result sort.")
        return

    f1, f2, f3 = st.columns(3)

    brand_options = sorted({
        row.get("brand")
        for row in results
        if row.get("brand")
    })

    model_options = sorted({
        row.get("model")
        for row in results
        if row.get("model")
    })

    status_options = sorted({
        row.get("comparison_status") or "UNKNOWN"
        for row in results
    })

    selected_brands = f1.multiselect(
        "Márka",
        brand_options,
        key="benchmark_brand_filter",
    )

    selected_models = f2.multiselect(
        "Modell",
        model_options,
        key="benchmark_model_filter",
    )

    selected_statuses = f3.multiselect(
        "Comparison status",
        status_options,
        key="benchmark_status_filter",
    )

    filtered = []

    for row in results:
        if (
            selected_brands
            and row.get("brand") not in selected_brands
        ):
            continue

        if (
            selected_models
            and row.get("model") not in selected_models
        ):
            continue

        comparison_status = (
            row.get("comparison_status")
            or "UNKNOWN"
        )

        if (
            selected_statuses
            and comparison_status not in selected_statuses
        ):
            continue

        filtered.append(row)

    table_rows = []

    for row in filtered:
        table_rows.append(
            {
                "Group": row.get("group_key"),
                "Pair status": row.get("pair_status"),
                "Brand": row.get("brand"),
                "Model": row.get("model"),
                "Fuel": row.get("fuel_type"),
                "Left": row.get("left_provider"),
                "Left advertised": row.get(
                    "left_advertised_monthly_fee_huf"
                ),
                "Right": row.get("right_provider"),
                "Right advertised": row.get(
                    "right_advertised_monthly_fee_huf"
                ),
                "Full comparison": row.get("comparison_status"),
                "Price comparable": row.get(
                    "price_comparison_allowed"
                ),
                "Winner": row.get("price_winner"),
                "Blockers": row.get("blocker_count"),
            }
        )

    table = pd.DataFrame(table_rows)

    if not table.empty:
        display = table.copy()

        display["Left advertised"] = display[
            "Left advertised"
        ].map(huf)

        display["Right advertised"] = display[
            "Right advertised"
        ].map(huf)

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Pair details")

    labels = {
        f"{row.get('group_key')} | "
        f"{row.get('left_provider')} ↔ {row.get('right_provider')} | "
        f"#{row.get('id')}": row
        for row in filtered
    }

    if not labels:
        st.info("Nincs a szűrésnek megfelelő benchmark pair.")
        return

    selected_label = st.selectbox(
        "Benchmark pair",
        tuple(labels.keys()),
        key="benchmark_pair_detail",
    )

    selected = labels[selected_label]

    d1, d2 = st.columns(2)

    with d1:
        st.metric(
            f"{selected.get('left_provider')} advertised",
            huf(
                selected.get(
                    "left_advertised_monthly_fee_huf"
                )
            ),
        )

        comparable = selected.get(
            "left_comparable_monthly_fee_huf"
        )

        if comparable is not None:
            st.metric(
                f"{selected.get('left_provider')} comparable",
                huf(comparable),
            )

    with d2:
        st.metric(
            f"{selected.get('right_provider')} advertised",
            huf(
                selected.get(
                    "right_advertised_monthly_fee_huf"
                )
            ),
        )

        comparable = selected.get(
            "right_comparable_monthly_fee_huf"
        )

        if comparable is not None:
            st.metric(
                f"{selected.get('right_provider')} comparable",
                huf(comparable),
            )

    if selected.get("price_comparison_allowed"):
        st.success(
            f"Price comparison allowed · Winner: "
            f"{selected.get('price_winner') or 'TIE'}"
        )
    else:
        st.warning(
            "Price ranking blocked by the evidence-aware comparison engine."
        )

    blockers = selected.get("blockers") or ()

    if blockers:
        st.markdown("#### Blockers")

        for blocker in blockers:
            code = blocker.get("code") or "UNKNOWN"
            message = blocker.get("message") or ""
            severity = blocker.get("severity") or "EVIDENCE"

            with st.expander(
                f"{code} · {severity}",
                expanded=True,
            ):
                st.write(message)

    response = selected.get("response")

    if response:
        with st.expander("Full comparison API payload"):
            st.json(response)


def render_offer(title, offer):
    st.subheader(title)
    st.caption(offer["provider"])

    vehicle = offer["vehicle"]
    st.markdown(
        f"### {vehicle.get('brand') or ''} {vehicle.get('model') or ''}"
    )
    st.write(f"**Kivitel:** {vehicle.get('trim') or '—'}")
    st.write(f"**Hajtás:** {vehicle.get('fuel_type') or '—'}")

    price = offer["price"]
    st.metric(
        "Hirdetett havidíj",
        huf(price.get("advertised_monthly_fee_huf")),
    )

    comparable = price.get("comparable_monthly_fee_huf")
    if comparable is not None:
        st.metric("Normalizált havidíj", huf(comparable))

    dp = price["down_payment"]

    if dp["status"] == "OBSERVED":
        if dp.get("percent") is not None:
            st.success(
                f"Induló befizetés: {dp['percent']:.0f}% · igazolt"
            )
        elif dp.get("amount_huf") is not None:
            st.success(
                f"Induló befizetés: {huf(dp['amount_huf'])} · igazolt"
            )
    else:
        st.warning("Induló befizetés: nem igazolt")

    basis = price.get("pricing_basis")
    if basis:
        st.caption(f"Financial evidence: {basis}")

    contract = offer["contract"]
    c1, c2 = st.columns(2)

    c1.metric(
        "Futamidő",
        f"{contract.get('duration_months') or '—'} hó",
    )

    c2.metric(
        "Futás",
        (
            f"{contract.get('mileage_km_per_year'):,} km/év".replace(",", " ")
            if contract.get("mileage_km_per_year")
            else "—"
        ),
    )

    if offer.get("source_url"):
        st.link_button(
            "Forrás",
            offer["source_url"],
            use_container_width=True,
        )


def render_dimensions(dimensions):
    st.subheader("Összehasonlíthatóság")

    labels = {
        "vehicle": "Járműazonosság",
        "variant": "Kivitel / variant",
        "services": "Szolgáltatások",
        "equipment": "Felszereltség",
        "contract": "Szerződés",
        "financial": "Pénzügyi feltételek",
    }

    for key, label in labels.items():
        status = dimensions.get(key, "UNKNOWN")
        st.write(
            f"{status_badge(status)} **{label}** — `{status}`"
        )


def render_blockers(blockers):
    st.subheader("Aktív blockerek")

    if not blockers:
        st.success("Nincs aktív blocker.")
        return

    for item in blockers:
        icon = "🔴" if item["severity"] == "HARD" else "🟠"

        with st.expander(
            f"{icon} {item['code']}",
            expanded=True,
        ):
            st.write(item["message"])
            st.caption(f"Súlyosság: {item['severity']}")


def render_live_comparison():
    st.header("Live Comparison")

    with st.sidebar:
        st.divider()
        st.caption("Live comparison beállítások")

        arval_url = st.text_area(
            "Arval URL",
            DEFAULT_ARVAL_URL,
            height=100,
        )

        ayvens_url = st.text_area(
            "Ayvens URL",
            DEFAULT_AYVENS_URL,
            height=80,
        )

        headless = st.checkbox(
            "Headless browser",
            value=False,
            help=(
                "Az Arval jelenleg nem mindig rendereli megbízhatóan "
                "az ajánlati oldalt headless Chromiumban."
            ),
        )

        run_button = st.button(
            "Live összehasonlítás futtatása",
            type="primary",
            use_container_width=True,
        )

    if run_button:
        with st.spinner(
            "Scraping → acquisition → enrichment → comparison..."
        ):
            try:
                run = LiveComparisonService().run(
                    arval_url=arval_url.strip(),
                    ayvens_url=ayvens_url.strip(),
                    headless=headless,
                )

                st.session_state["comparison_payload"] = (
                    run.response.to_dict()
                )
                st.session_state["acquisition_status"] = (
                    run.acquisition.execution.status
                )

            except Exception as exc:
                st.exception(exc)

    data = st.session_state.get("comparison_payload")

    if data is None:
        st.info(
            "A bal oldali panelen indítsd el a live összehasonlítást."
        )
        return

    if data["price_comparison_allowed"]:
        st.success(
            "Ár-összehasonlítás engedélyezett · "
            f"Győztes: {data.get('price_winner') or 'TIE'}"
        )
    else:
        st.warning(
            "Árgyőztes még nem állapítható meg biztonságosan."
        )

    left_col, right_col = st.columns(2)

    with left_col:
        render_offer("Bal ajánlat", data["left_offer"])

    with right_col:
        render_offer("Jobb ajánlat", data["right_offer"])

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        render_dimensions(data["dimensions"])

    with c2:
        render_blockers(data["blockers"])

    with st.expander("API payload"):
        st.json(data)


@st.cache_data(ttl=60)
def load_market_data():
    return MarketDashboardService().load()


@st.cache_data(ttl=60)
def load_benchmark_data():
    return BenchmarkDashboardService().load()


def main():
    st.title("Fleet Intelligence")
    st.caption(
        "Evidence-aware flottapiaci intelligence cockpit"
    )

    page = st.sidebar.radio(
        "Nézet",
        (
            "Market Overview",
            "Provider Comparison",
            "Vehicle / Offer Explorer",
            "Price History & Changes",
            "Benchmark Intelligence",
            "Live Comparison",
        ),
    )

    if st.sidebar.button(
        "Piaci adatok frissítése",
        use_container_width=True,
    ):
        load_market_data.clear()
        load_benchmark_data.clear()

    data = load_market_data()

    if page == "Market Overview":
        render_market_overview(data)
    elif page == "Provider Comparison":
        render_provider_comparison(data)
    elif page == "Vehicle / Offer Explorer":
        render_offer_explorer(data)
    elif page == "Price History & Changes":
        render_price_history(data)
    elif page == "Benchmark Intelligence":
        render_benchmark_intelligence()
    else:
        render_live_comparison()


if __name__ == "__main__":
    main()
