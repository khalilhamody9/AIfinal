import pressure_plate
import ex2
import test_file
import time

example1 = {
    'chosen_action_prob': {
        'U': [0.9, 0.05, 0.05, 0],
        'L': [0.1, 0.8, 0.075, 0.025],
        'R': [0.05, 0.05, 0.85, 0.05],
        'D': [0.05, 0.1, 0.15, 0.7]
    },
    'finished_reward': 350,
    'opening_door_reward': {
        10: 5, 11: 7, 12: 9, 13: 11, 14: 13,
        15: 15, 16: 17, 17: 19, 18: 21, 19: 23
    },
    'step_punishment': -2,
    'seed': 42
}

example2 = {
    'chosen_action_prob': {
        'U': [0.6, 0.05, 0.05, 0.3],
        'L': [0, 0.9, 0.075, 0.025],
        'R': [0.25, 0.2, 0.3, 0.25],
        'D': [0.05, 0.138, 0.15, 0.662]
    },
    'finished_reward': 200,
    'opening_door_reward': {
        10: -3, 11: 2, 12: 15, 13: -6, 14: 3,
        15: -10, 16: 17, 17: 0, 18: 1, 19: -2
    },
    'step_punishment': -2,
    'seed': 123
}

def solve(game: pressure_plate.Game):
    policy = ex2.Controller(game)
    for _ in range(game.get_max_steps()):
        game.submit_next_action(chosen_action=policy.choose_next_action(game.get_current_state()))
        if game.get_current_state()[3]:
            break
    result = game.get_current_state()
    print('Game result:\n\tMap state ->\n', result[0])
    print('\tFinished in', result[2], 'steps.')
    print('\tReward result ->', game.get_current_reward())
    print("Game finished ", "" if result[-1] else "un", "successfully.", sep='')
    game.show_history()
    return result[-1]  # True if successful

def main():
    debug_mode = False  # Set to True to enable debug prints
    enabled_tests = [
        1, 2, 3, 4, 5, 6, 7, 8, 9,
        11, 12, 13, 14, 15, 16, 17, 18, 19, 20
    ]

    base_example = example1  # Choose example1 or example2
    num_runs = 30  # Number of seeds to run for each problem

    # Store summary for all problems
    summary = []

    for idx in enabled_tests:
        print(f"\n=== Running test_problem{idx} ===")
        problem = getattr(test_file, f"test_problem{idx}")

        success_count = 0
        total_reward = 0
        total_steps = 0
        total_time = 0

        for seed in range(num_runs):
            example = base_example.copy()
            example['seed'] = seed

            start_time = time.time()
            game = pressure_plate.create_pressure_plate_game((100 + idx * 10 + seed, problem, example, debug_mode))
            result = solve(game)
            elapsed = time.time() - start_time

            total_time += elapsed
            if result:
                success_count += 1
            total_reward += game.get_current_reward()
            total_steps += game.get_current_state()[2]

        avg_reward = total_reward / num_runs
        avg_steps = total_steps / num_runs
        avg_time = total_time / num_runs

        print(f"=== Results for problem {idx} ===")
        print(f"✔ Success rate: {success_count}/{num_runs}")
        print(f"✔ Avg reward: {avg_reward:.2f}")
        print(f"✔ Avg steps: {avg_steps:.2f}")
        print(f"✔ Avg time: {avg_time:.2f} seconds")

        summary.append((idx, success_count, avg_reward, avg_steps, avg_time))

    # Print final summary table
    print("\n=== Final Summary ===")
    print(f"{'Problem':>8} | {'Success':>9} | {'Avg Reward':>11} | {'Avg Steps':>10} | {'Avg Time':>9}")
    print("-" * 60)
    for idx, success, avg_reward, avg_steps, avg_time in summary:
        print(f"{idx:>8} | {success:>9}/{num_runs} | {avg_reward:>11.2f} | {avg_steps:>10.2f} | {avg_time:>9.2f}")



if __name__ == "__main__":
    main()
