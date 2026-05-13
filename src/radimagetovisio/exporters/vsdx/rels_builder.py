from __future__ import annotations


class RelsBuilder:
    def __init__(self) -> None:
        self._counter = 0
        self._entries: list[dict[str, str]] = []

    def next_id(self) -> str:
        self._counter += 1
        return f"rId{self._counter}"

    def add(self, rel_type: str, target: str, target_mode: str | None = None) -> str:
        rid = self.next_id()
        entry: dict[str, str] = {"Id": rid, "Type": rel_type, "Target": target}
        if target_mode:
            entry["TargetMode"] = target_mode
        self._entries.append(entry)
        return rid

    def to_xml(self) -> str:
        lines = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
        ]
        for entry in self._entries:
            attrs = " ".join(f'{k}="{v}"' for k, v in entry.items())
            lines.append(f"  <Relationship {attrs}/>")
        lines.append("</Relationships>")
        return "\n".join(lines) + "\n"

    def __len__(self) -> int:
        return len(self._entries)
