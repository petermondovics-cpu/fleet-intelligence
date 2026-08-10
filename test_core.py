from core import FleetIQPlugin, PluginRegistry


class TestPlugin(FleetIQPlugin):
    name = "test"

    def execute(self):
        return "FleetIQ works!"


def main():
    registry = PluginRegistry()

    plugin = TestPlugin()

    registry.register(plugin)

    print("Registered plugins:")
    print(registry.names())

    print("\nPlugin execution:")
    print(registry.get("test").execute())


if __name__ == "__main__":
    main()