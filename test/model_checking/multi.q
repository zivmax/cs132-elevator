//This file was generated from (Academic) UPPAAL 5.0.0 (rev. 714BA9DB36F49691), 2023-06-21

/*
Safety: Elevators stay within floor bounds 0-3
*/
A[] (forall (i : int[0, NUM_ELEVATORS-1]) current_floor[i] >= MIN_FLOOR && current_floor[i] <= MAX_FLOOR)

/*
Safety: Task queue never exceeds maximum
*/
A[] (forall (i : int[0, NUM_ELEVATORS-1]) task_queue_size[i] <= MAX_TASKS)

/*
Safety: Doors closed during movement
*/
A[] (forall (i : int[0, NUM_ELEVATORS-1]) (elevator_state[i] == MOVING_UP || elevator_state[i] == MOVING_DOWN) imply door_state[i] == DOOR_CLOSED)

/*
Safety: Doors only open when elevator is idle
*/
A[] (forall (i : int[0, NUM_ELEVATORS-1]) door_state[i] == DOOR_OPEN imply elevator_state[i] == IDLE)

/*
Safety: Floor arrival only announced when idle
*/
A[] (forall (i : int[0, NUM_ELEVATORS-1]) floor_arrival_announced[i] imply elevator_state[i] == IDLE)

/*
Reachability: Elevator 0 can reach floor 3
*/
E<> (current_floor[0] == MAX_FLOOR)

/*
Reachability: Elevator 0 can reach floor 0
*/
E<> (current_floor[0] == MIN_FLOOR)

/*
Reachability: Tasks can be assigned
*/
E<> (task_queue_size[0] > 0)

/*
System is deadlock-free
*/
A[] not deadlock
