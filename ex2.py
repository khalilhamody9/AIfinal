import pressure_plate
import numpy as np
import ex1
import search
from collections import deque

id = ["212923775"]

class Controller:
    """Controller for pressure plate game with adaptive replanning."""

    def __init__(self, game: pressure_plate.Game):
        """Initialize the controller with game parameters."""
        self.game = game
        self.action_plan = deque()  # Using deque instead of list for efficiency
        self.last_position = None
        self.last_intended_move = None
        self.plan_cache = {}  # Cache solutions
        self.replan_count = 0
        self.stuck_counter = 0
        
        # Get MDP model for future use (even if not using full MDP)
        model = game.get_model()
        self.action_probabilities = model['chosen_action_prob']
        
    def choose_next_action(self, state):
        """Select next action with drift detection and replanning."""
        board, current_pos, steps_taken, is_done, is_success = state
        board_tuple = self._board_to_tuple(board)
        
        # Check if we drifted from intended path
        if self._has_drifted(current_pos):
            self.action_plan.clear()  # Clear current plan
            self.replan_count += 1
            
        # Check if stuck in same position
        if self.last_position == current_pos:
            self.stuck_counter += 1
            if self.stuck_counter > 3:
                self.action_plan.clear()
                self.stuck_counter = 0
        else:
            self.stuck_counter = 0
            
        # Generate new plan if needed
        if not self.action_plan:
            self.action_plan = self._generate_plan(board_tuple, current_pos)
            if not self.action_plan:
                # No valid plan, try random move
                return self._emergency_move(board, current_pos)
        
        # Execute next action from plan
        next_move = self.action_plan.popleft()
        self.last_intended_move = next_move
        self.last_position = current_pos
        
        return next_move
    
    def _has_drifted(self, current_pos):
        """Check if agent moved as intended."""
        if not self.last_position or not self.last_intended_move:
            return False
            
        expected_pos = self._calculate_expected_position(
            self.last_position, self.last_intended_move
        )
        return current_pos != expected_pos
    
    def _calculate_expected_position(self, from_pos, action):
        """Calculate where agent should be after action."""
        row, col = from_pos
        movements = {
            'U': (-1, 0),
            'D': (1, 0), 
            'L': (0, -1),
            'R': (0, 1)
        }
        
        if action in movements:
            dr, dc = movements[action]
            return (row + dr, col + dc)
        return from_pos
    
    def _board_to_tuple(self, board):
        """Convert board to hashable tuple for caching."""
        return tuple(tuple(row) for row in board)
    
    def _generate_plan(self, board_tuple, current_pos):
        """Generate action plan using A* search."""
        # Check cache first
        cache_key = (board_tuple, tuple(current_pos))
        if cache_key in self.plan_cache:
            cached_plan = self.plan_cache[cache_key]
            return deque(cached_plan) if cached_plan else deque()
        
        try:
            # Create problem and solve
            problem = ex1.create_pressure_plate_problem(board_tuple)
            
            # Adjust max nodes based on board size
            board_area = len(board_tuple) * len(board_tuple[0])
            max_search_nodes = 50000 if board_area <= 100 else 150000
            
            # Run A* search
            search_result = search.astar_search(
                problem, 
                problem.h, 
                max_expanded=max_search_nodes
            )
            
            # Extract solution
            if search_result:
                solution_path = self._extract_path(search_result)
                if solution_path:
                    self.plan_cache[cache_key] = solution_path
                    return deque(solution_path)
                    
        except Exception:
            # Silently handle errors
            pass
            
        # Cache empty result
        self.plan_cache[cache_key] = []
        return deque()
    
    def _extract_path(self, search_result):
        """Extract action sequence from search result."""
        # Handle different return formats from search
        if isinstance(search_result, tuple):
            node = search_result[0] if len(search_result) > 0 else None
        else:
            node = search_result
            
        if node and hasattr(node, 'path'):
            path_nodes = node.path()
            path_nodes.reverse()  # Get from start to goal
            
            # Extract actions, skip first node (initial state)
            actions = []
            for node in path_nodes[1:]:
                if hasattr(node, 'action') and node.action:
                    actions.append(node.action)
            return actions
            
        return []
    
    def _emergency_move(self, board, current_pos):
        """Make emergency move when no plan available."""
        # Try to move toward any empty space
        row, col = current_pos
        possible_moves = []
        
        for action, (dr, dc) in [('U', (-1, 0)), ('D', (1, 0)), 
                                  ('L', (0, -1)), ('R', (0, 1))]:
            new_row, new_col = row + dr, col + dc
            
            # Check bounds
            if 0 <= new_row < len(board) and 0 <= new_col < len(board[0]):
                cell = board[new_row][new_col]
                # Check if can move there (empty, goal, or plate)
                if cell in [98, 0, 2] or (20 <= cell <= 29):
                    possible_moves.append(action)
                    
        if possible_moves:
            # Prefer moves that haven't been tried recently
            return np.random.choice(possible_moves)
        
        # Last resort - random action
        return np.random.choice(['U', 'D', 'L', 'R'])