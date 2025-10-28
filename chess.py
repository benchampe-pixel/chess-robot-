# Polyglot piece names by index
pieces = [
    "BN", "WN", "BB", "WB", "BQ", "WQ",
    "BK", "WK", "BR", "WR", "BP", "WP"
]
def piece_to_fen(name):
    mapping = {
        "WP": "P", "WN": "N", "WB": "B", "WR": "R", "WQ": "Q", "WK": "K",
        "BP": "p", "BN": "n", "BB": "b", "BR": "r", "BQ": "q", "BK": "k",
    }
    return mapping.get(name, "?")

def board_to_fen(board):
    fen_rows = []
    for row in board:
        fen_row = ""
        empty = 0
        for cell in row:
            if cell == "":
                empty += 1
            else:
                if empty:
                    fen_row += str(empty)
                    empty = 0
                fen_row += cell
        if empty:
            fen_row += str(empty)
        fen_rows.append(fen_row)
    return "/".join(fen_rows)
