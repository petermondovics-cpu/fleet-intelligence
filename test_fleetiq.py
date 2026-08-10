from core import FleetIQ, FleetIQPlugin


class TestPlugin(FleetIQPlugin):
    name = "test"

    def execute(self):
        return "FleetIQ works!"


def main():
    fleet = FleetIQ()

    plugin = TestPlugin()

    fleet.register(plugin)

    print("FleetIQ plugins:")
    print(fleet.plugins())


if __name__ == "__main__":
    main()