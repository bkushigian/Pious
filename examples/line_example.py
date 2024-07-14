"""
This example loads a test tree packaged in resources, loads all nodes, and
prints all lines.
"""

from pious.pio.line import Line

line = Line("r:0")
print("Line:", line)
print("  IP?                 ", line.is_ip())
print("  Current Street?     ", line.current_street())
print("  Facing Bet?         ", line.is_facing_bet())

line = Line("r:0:c")
print("Line:", line)
print("  IP?                 ", line.is_ip())
print("  Current Street?     ", line.current_street())
print("  Facing Bet?         ", line.is_facing_bet())

line = Line("r:0:c:b12")
print("Line:", line)
print("  IP?                 ", line.is_ip())
print("  Current Street?     ", line.current_street())
print("  Facing Bet?         ", line.is_facing_bet())

line = Line("r:0:c:b12:c:c:b77:b221")
print("Line:", line)
print("  IP?                 ", line.is_ip())
print("  Current Street?     ", line.current_street())
print("  Facing Bet?         ", line.is_facing_bet())

line = Line("r:0:c:b12:c:c:b77:b221:c:c")
print("Line:", line)
print("  IP?                 ", line.is_ip())
print("  Current Street?     ", line.current_street())
print("  Actions:            ", line.actions)
print("  Streets as Actions: ", line.streets_as_actions)
print("  Streets as Lines:   ", line.streets_as_lines)
print("  Facing Bet?         ", line.is_facing_bet())
