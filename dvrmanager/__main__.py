from dvrmanager import logs
from dvrmanager.application import application
from dvrmanager.settings import Settings
from dvrmanager.window import MainWindow


def main():
    logs.configure()
    settings = Settings.load()
    with application() as app:
        window = MainWindow(app, settings)
        window.show()


if __name__ == '__main__':
    main()
