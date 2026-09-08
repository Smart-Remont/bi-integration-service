"""Group flat flat_guid remont-info rows by room.

`rest.ddu_flat_remont_info` returns one row per (room, param) pair. This mirrors
legacy PHP `_dduFlatRemontInfoNestByRoom()`: group into `rooms[]`, each carrying
its own `params[]`, sorted by room id then by param id (nulls last / zero-first).
"""

from typing import Any

Row = dict[str, Any]


def nest_flat_remont_info_by_room(rows: list[Row]) -> dict[str, Any]:
    if not rows:
        return {"client_request_id": None, "remont_id": None, "rooms": []}

    first = rows[0]
    rooms_by_id: dict[object, dict[str, Any]] = {}

    for row in rows:
        room_id = row.get("room_id")
        room = rooms_by_id.setdefault(
            room_id,
            {
                "room_id": room_id,
                "room_name": row.get("room_name"),
                "params": [],
            },
        )
        object_param_id = row.get("object_param_id")
        if object_param_id is None:
            object_param_id = row.get("fix_param_id")

        room["params"].append(
            {
                "object_param_id": object_param_id,
                "param_id": row.get("param_id"),
                "param_name": row.get("param_name"),
                "param_code": row.get("param_code"),
                "param_value": row.get("param_value"),
            },
        )

    rooms = sorted(rooms_by_id.values(), key=lambda room: _room_sort_key(room["room_id"]))
    for room in rooms:
        room["params"].sort(key=lambda param: _param_sort_key(param["object_param_id"]))

    return {
        "client_request_id": first.get("client_request_id"),
        "remont_id": first.get("remont_id"),
        "rooms": rooms,
    }


def _room_sort_key(room_id: object) -> tuple[int, int]:
    if room_id is None:
        return (1, 0)
    return (0, int(room_id))


def _param_sort_key(object_param_id: object) -> int:
    if object_param_id is None:
        return 0
    return int(object_param_id)
