#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from engine import db as db_module
from engine.simulations import simulate_road_closure, simulate_new_facility


def cmd_list_roads(args, conn):
    roads = db_module.get_all_roads(conn)
    if args.road_class:
        roads = [r for r in roads if r["road_class"] == args.road_class]
    for r in roads:
        print(f"  [{r['id']:>3}] {r['name']:<20} {r['road_class']:<10} "
              f"{r['length_m']:.0f}m  {r['speed_kmph']}km/h  cap={r['capacity_vph']}vph")


def cmd_close_road(args, conn):
    road_id = args.road_id
    if not road_id and args.road_name:
        road = db_module.get_road_by_name(conn, args.road_name)
        if not road:
            print(f"No road named '{args.road_name}' found.", file=sys.stderr)
            sys.exit(1)
        road_id = road["id"]
    print(json.dumps(simulate_road_closure(conn, road_id), indent=2))


def cmd_new_facility(args, conn):
    result = simulate_new_facility(conn, args.type, args.lat, args.lon, args.name)
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description="CityMind Phase 1 simulation CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list-roads")
    p_list.add_argument("--class", dest="road_class", choices=["arterial", "collector", "local"])

    p_close = sub.add_parser("close-road")
    p_close.add_argument("--road-id", type=int)
    p_close.add_argument("--road-name", type=str)

    p_new = sub.add_parser("new-facility")
    p_new.add_argument("--type", required=True,
                        choices=["hospital", "school", "fire_station", "police_station", "bus_stop", "parking"])
    p_new.add_argument("--lat", type=float, required=True)
    p_new.add_argument("--lon", type=float, required=True)
    p_new.add_argument("--name", type=str, default=None)

    args = parser.parse_args()
    conn = db_module.connect()

    if args.command == "list-roads":
        cmd_list_roads(args, conn)
    elif args.command == "close-road":
        cmd_close_road(args, conn)
    elif args.command == "new-facility":
        cmd_new_facility(args, conn)


if __name__ == "__main__":
    main()