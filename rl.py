import numpy as np
import random

# Environment settings
n_states = 6        # positions: 0,1,2,3,4,5
actions = [0, 1]    # 0 = left, 1 = right
goal_state = 5
alpha = 0.1         # learning rate
gamma = 0.9         # discount factor
epsilon = 0.3       # exploration rate
episodes = 100

# Initialize Q-table
Q = np.zeros((n_states, len(actions)))

# Training loop
for episode in range(episodes):
    state = 0  # start position
    done = False
    
    while not done:
        # Choose action (explore or exploit)
        if random.uniform(0, 1) < epsilon:
            action = random.choice(actions)  # explore
        else:
            action = np.argmax(Q[state])     # exploit best action
        
        # Take action → observe next state and reward
        if action == 1:  # move right
            next_state = state + 1
        else:            # move left
            next_state = state - 1
        
        # Reward logic
        if next_state == goal_state:
            reward = 1
            done = True
        elif next_state < 0 or next_state > goal_state:
            reward = -1
            done = True
        else:
            reward = 0
        
        # Q-learning update rule
        Q[state, action] = Q[state, action] + alpha * (
            reward + gamma * np.max(Q[next_state]) - Q[state, action]
        )
        
        state = next_state  # move to next state

# Show learned Q-values
print("Learned Q-table:")
print(Q)

# Test the learned policy
state = 0
print("\nAgent’s path to goal:")
path = [state]
while state != goal_state:
    action = np.argmax(Q[state])
    state = state + 1 if action == 1 else state - 1
    path.append(state)
    if state < 0 or state > goal_state:
        break

print(" → ".join(map(str, path)))
