"""Characters, stakes, and future modifier data for Crab Checkers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Character:
    key: str
    name: str
    short_name: str
    tagline: str
    power_name: str
    power_text: str
    color: tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class Stake:
    key: str
    label: str
    depth: int
    description: str


@dataclass(frozen=True, slots=True)
class Modifier:
    key: str
    name: str
    text: str
    enabled: bool = False


CHARACTERS = (
    Character(
        key="bear",
        name="The Patient Bear",
        short_name="Bear",
        tagline="Reads the tide before moving.",
        power_name="Hibernate",
        power_text="Future power: defensive bonuses after blocking a line.",
        color=(211, 83, 71),
    ),
    Character(
        key="hat",
        name="The Hat Player",
        short_name="Hat",
        tagline="A table shark with a slippery plan.",
        power_name="Side Glance",
        power_text="Future power: preview or bend one slide each round.",
        color=(70, 104, 210),
    ),
    Character(
        key="lamp",
        name="The Lantern Keeper",
        short_name="Lamp",
        tagline="Makes quiet moves look dangerous.",
        power_name="Lantern Tell",
        power_text="Future power: reveal the strongest threat on the board.",
        color=(218, 168, 62),
    ),
)

STAKES = (
    Stake(
        key="easy",
        label="Easy Stake",
        depth=0,
        description="A forgiving opponent that plays loose, legal moves.",
    ),
    Stake(
        key="mid",
        label="Mid Stake",
        depth=2,
        description="A tactical opponent that sees a few moves ahead.",
    ),
    Stake(
        key="hard",
        label="Hard Stake",
        depth=4,
        description="A sharper opponent with deeper search.",
    ),
)

MODIFIERS = (
    Modifier(
        key="reef_drift",
        name="Reef Drift",
        text="Future joker: once per game, stop a sliding crab early.",
    ),
    Modifier(
        key="side_step",
        name="Side Step",
        text="Future joker: allow one diagonal slide.",
    ),
    Modifier(
        key="tide_turn",
        name="Tide Turn",
        text="Future joker: flip a one-turn rule at the table.",
    ),
)


def get_character(key: str) -> Character:
    for character in CHARACTERS:
        if character.key == key:
            return character
    raise KeyError(key)


def get_stake(key: str) -> Stake:
    for stake in STAKES:
        if stake.key == key:
            return stake
    raise KeyError(key)

