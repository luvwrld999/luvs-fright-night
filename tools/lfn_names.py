"""Stage names, read from the generated level table."""

NAMES = [
    'Chapel of the Mirror',
    'The Long Gallery',
    'Superbia',
    'The Counting Floor',
    'Vault of Small Coins',
    'Avaritia',
    'Thorn Walk',
    'The Lantern Beds',
    'Luxuria',
    'Green Water',
    'What He Has',
    'Invidia',
    'The Larder',
    'Second Helpings',
    'Gula',
    'Cinderpath',
    'The Faultline',
    'Ira',
    'Dust Rooms',
    'Nothing Stirs',
    'Acedia',
    'The Descent',
    'Below Everything',
    'Hades',
    'Nine Nine Nine',
    'The Long Way Round',
    'Straight Down',
]


def of(index):
    return NAMES[index] if 0 <= index < len(NAMES) else "?"
