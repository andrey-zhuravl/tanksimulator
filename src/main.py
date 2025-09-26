from __future__ import annotations

import argparse

from tanks import config
from tanks.client_ai import AITankClient
from tanks.client_keyboard import KeyboardTankClient
from tanks.server import TankGameServer


def main() -> None:
    parser = argparse.ArgumentParser(description="Tank simulator client/server entry point")
    parser.add_argument(
        "mode",
        choices=["server", "client", "ai"],
        help="Что запустить: сервер, клиент с клавиатурой или AI-клиент",
    )
    parser.add_argument("--host", default=config.DEFAULT_SERVER_HOST, help="Адрес сервера")
    parser.add_argument("--port", type=int, default=config.DEFAULT_SERVER_PORT, help="Порт сервера")
    parser.add_argument(
        "--team",
        choices=["player", "enemy"],
        default="player",
        help="Команда, за которую будет играть клиент",
    )

    args = parser.parse_args()

    if args.mode == "server":
        TankGameServer(host=args.host, port=args.port).run()
    elif args.mode == "client":
        KeyboardTankClient(host=args.host, port=args.port, team=args.team).run()
    else:
        AITankClient(host=args.host, port=args.port, team=args.team).run()


if __name__ == "__main__":
    main()
