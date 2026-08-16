from market_intelligence.unified_market_collector import UnifiedMarketCollector

class ScraperManager:
    def run(self):
        collector = UnifiedMarketCollector()

        try:
            result = collector.run()

            print("\n" + "=" * 72)
            print("UNIFIED MARKET COLLECTION")
            print("=" * 72)
            print("Run:", result.run_id)
            print("Status:", result.status)
            print("Offers:", result.total_offers)

            for item in result.provider_results:
                print(
                    f"- {item.provider}: {item.status} "
                    f"| raw={item.raw_count} "
                    f"| saved={item.normalized_count}"
                )
                if item.diagnostic:
                    print("  diagnostic:", item.diagnostic)

            return result
        finally:
            collector.close()
