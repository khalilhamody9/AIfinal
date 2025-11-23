import search

id = ["212923775"]

CELL_EMPTY, CELL_WALL, CELL_PATH = 0, 99, 98
PLAYER, GOAL = 1, 2
DOORS_LOCKED = list(range(40, 50))
SWITCH_PLATES = list(range(20, 30))
PUSH_BLOCKS = list(range(10, 20))

MOVES = {
    "R": (0, 1),
    "L": (0, -1),
    "U": (1, 0),
    "D": (-1, 0)
}

def The_Mask(layout):
    bitmask = 0
    i = 0
    while i < len(layout):
        line = layout[i]
        j = 0
        while j < len(line):
            cell = line[j]
            if cell in SWITCH_PLATES:
                bitmask |= 1 << (cell % 10)
            j += 1
        i += 1
    return bitmask

class PressurePlateProblem(search.Problem):
    def __init__(self, initial_state):
        self.layout = initial_state
        self._base_layout = [list(row) for row in initial_state]
        self.height = len(initial_state)
        self.width = len(initial_state[0])

        self.goal_position = None
        self.visited_states = set()
        self.door_positions = []
        self.plate_positions = []
        movable_blocks = []
        player_start = None

        i = 0
        while i < self.height:
            j = 0
            while j < self.width:
                value = initial_state[i][j]
                if value == GOAL:
                    self.goal_position = (i, j)
                elif value == PLAYER:
                    player_start = (i, j)
                    self._base_layout[i][j] = CELL_PATH
                elif value in PUSH_BLOCKS:
                    movable_blocks.append((i, j, value % 10))
                    self._base_layout[i][j] = CELL_PATH
                elif value in SWITCH_PLATES:
                    self.plate_positions.append((i, j, value % 10))
                elif value in DOORS_LOCKED:
                    self.door_positions.append((i, j, value % 10))
                j += 1
            i += 1

        plate_counts = {}
        i = 0
        while i < len(initial_state):
            row = initial_state[i]
            j = 0
            while j < len(row):
                val = row[j]
                if val in SWITCH_PLATES:
                    t = val % 10
                    plate_counts[t] = plate_counts.get(t, 0) + 1
                j += 1
            i += 1

        self.plate_activation_requirements = plate_counts
        self.initial_mask = The_Mask(initial_state)

        initial = (player_start, tuple(sorted(movable_blocks)), frozenset(), frozenset(), self.initial_mask)
        super().__init__(initial, goal=self.goal_position)

    def pos(self, state):
        player_pos = state[0]
        blocks = list(state[1])
        open_doors = set(state[2])
        plate_states = dict(state[3])
        view = [list(row) for row in self._base_layout]

        i = 0
        while i < len(self.door_positions):
            y, x, k = self.door_positions[i]
            if k in open_doors:
                view[y][x] = CELL_PATH
            i += 1



        i = 0
        while i < len(blocks):
            y, x, t = blocks[i]
            view[y][x] = 10 + t
            i += 1
        i = 0
        while i < len(self.plate_positions):
            y, x, k = self.plate_positions[i]
            if plate_states.get(k, 0) == self.plate_activation_requirements[k]:
                view[y][x] = CELL_WALL
            i += 1

        view[player_pos[0]][player_pos[1]] = PLAYER
        return view

    def _apply_direction(self, state, direction):
        if len(state) == 4:
            player_pos, blocks, open_doors, plate_states = state
            mask = self.initial_mask
        else:
            player_pos, blocks, open_doors, plate_states, mask = state

        r, c = player_pos
        dr, dc = MOVES[direction]
        mid = (r + dr, c + dc)
        far = (r + 2 * dr, c + 2 * dc)

        if not (0 <= mid[0] < self.height and 0 <= mid[1] < self.width):
            return []

        view = self.pos(state)
        mid_val = view[mid[0]][mid[1]]
        far_val = view[far[0]][far[1]] if 0 <= far[0] < self.height and 0 <= far[1] < self.width else CELL_WALL

        if (
            mid_val == CELL_WALL or
            mid_val in SWITCH_PLATES or
            (mid_val in DOORS_LOCKED and (mid_val % 10) not in open_doors) or
            (mid_val in PUSH_BLOCKS and (
                far_val == CELL_WALL or
                far_val in PUSH_BLOCKS or
                (far_val in SWITCH_PLATES and (mid_val % 10 != far_val % 10))
            ))
        ):
            return []

        blocks = list(blocks)
        open_doors = set(open_doors)
        plate_states = dict(plate_states)
        results = []

        if mid_val in [CELL_PATH, GOAL]:
            new_state = (mid, tuple(sorted(blocks)), frozenset(open_doors), frozenset(plate_states.items()), mask)
            if (direction, new_state) not in self.visited_states:
                self.visited_states.add((direction, new_state))
                results.append((direction, new_state))

        elif mid_val in PUSH_BLOCKS:
            block_type = mid_val % 10
            if (mid[0], mid[1], block_type) in blocks:
                blocks.remove((mid[0], mid[1], block_type))
                if far_val == CELL_PATH:
                    blocks.append((far[0], far[1], block_type))
                elif far_val in SWITCH_PLATES and block_type == far_val % 10:
                    plate_states[block_type] = plate_states.get(block_type, 0) + 1
                    if plate_states[block_type] == self.plate_activation_requirements[block_type]:
                        open_doors.add(block_type)
                        mask &= ~(1 << block_type)
                new_state = (mid, tuple(sorted(blocks)), frozenset(open_doors), frozenset(plate_states.items()), mask)
                if (direction, new_state) not in self.visited_states:
                    self.visited_states.add((direction, new_state))
                    results.append((direction, new_state))

        return results

    def successor(self, state):
        directions = list(MOVES.keys())
        i = 0
        result = []
        while i < len(directions):
            result.extend(self._apply_direction(state, directions[i]))
            i += 1
        return result
    
    def _get_blocking_doors(self, state):
        """Find doors that block path to goal using BFS."""
        (agent_pos, blocks, open_doors, _, _) = state if len(state) == 5 else (*state, self.initial_mask)
        
        # BFS from goal to agent
        from collections import deque
        queue = deque([self.goal_position])
        visited = {self.goal_position}
        blocking_doors = set()
        
        # Get current view
        view = self.pos(state)
        
        while queue:
            pos = queue.popleft()
            
            # If we reached agent, path exists
            if pos == agent_pos:
                return set()  # No blocking doors
            
            # Try all directions
            for dr, dc in MOVES.values():
                new_pos = (pos[0] + dr, pos[1] + dc)
                
                # Check bounds
                if not (0 <= new_pos[0] < self.height and 0 <= new_pos[1] < self.width):
                    continue
                
                if new_pos in visited:
                    continue
                
                cell = view[new_pos[0]][new_pos[1]]
                
                # Check if passable
                if cell == CELL_WALL:
                    continue
                elif cell in DOORS_LOCKED and (cell % 10) not in open_doors:
                    blocking_doors.add(cell % 10)
                    continue
                elif cell in PUSH_BLOCKS:
                    continue  # Can't pass through blocks
                else:
                    # Can pass (empty, path, goal, plate)
                    visited.add(new_pos)
                    queue.append(new_pos)
        
        # No path found, return blocking doors
        return blocking_doors

    def h(self, node):
        state = node.state
        (r, c), blocks, open_doors, _, mask = state if len(state) == 5 else (*state, self.initial_mask)
        
        # Base: Manhattan distance to goal
        h_goal = abs(r - self.goal_position[0]) + abs(c - self.goal_position[1])
        
        # Check if path to goal is blocked by doors
        blocking_doors = self._get_blocking_doors(state)
        if blocking_doors:
            # Heavy penalty for blocked paths
            h_goal += len(blocking_doors) * 50
        
        # If doors are locked, add penalty
        if mask != 0:
            # Count unactivated plates
            num_plates = bin(mask).count("1")
            
            # Simple heuristic: for each block, add minimum distance to any matching plate
            h_blocks = 0
            for block_r, block_c, block_type in blocks:
                # Only consider blocks that need to be moved
                if mask & (1 << block_type):
                    # Find closest matching plate
                    min_dist = float('inf')
                    for plate_r, plate_c, plate_type in self.plate_positions:
                        if block_type == plate_type:
                            dist = abs(block_r - plate_r) + abs(block_c - plate_c)
                            min_dist = min(min_dist, dist)
                    if min_dist != float('inf'):
                        h_blocks += min_dist
            
            # Return weighted sum
            return h_goal + num_plates * 10 + h_blocks
        else:
            # All doors open, just go to goal
            return h_goal

    def goal_test(self, state):
        if state[0] == self.goal_position:
            return True
        return False

def create_pressure_plate_problem(game):
    return PressurePlateProblem(game)

if __name__ == "__main__":
    pass