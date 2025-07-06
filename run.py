import argparse
import importlib

AVAILABLE_BOTS = {
    'DS': 'bots.DS.bot',
    'DSA': 'bots.DSA.bot',
    'DSS': 'bots.DSS.bot',
}

def main():
    parser = argparse.ArgumentParser(description='Run selected telegram bot')
    parser.add_argument('bot', choices=AVAILABLE_BOTS, help='Bot name to run')
    args = parser.parse_args()
    module = importlib.import_module(AVAILABLE_BOTS[args.bot])
    print(f"Запуск бота {args.bot}")
    if hasattr(module, 'main'):
        module.main()
    else:
        raise SystemExit(f"Module {AVAILABLE_BOTS[args.bot]} has no main()")

if __name__ == '__main__':
    main()
