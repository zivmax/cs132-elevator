// This file was generated from (Academic) UPPAAL 5.0.0

/*
Risk 1: Each passenger’s calls eventually leads them to ride
*/
A<> (callPlacedUp[0] || callPlacedDown[0]) imply (P0.Riding) // Passenger 0 call is serviced
A<> (callPlacedUp[1] || callPlacedDown[1]) imply (P1.Riding) // Passenger 1 call is serviced
A<> (callPlacedUp[2] || callPlacedDown[2]) imply (P2.Riding) // Passenger 2 call is serviced

/*
Risk 2: Elevator stays in normal range
*/
A[] (El.c_floor >= MIN_FLOOR && El.c_floor <= MAX_FLOOR) // Elevator always within -1..3

/*
Risk 3: Each passenger eventually arrives
*/
A<> P0.Riding imply P0.Arrived // Passenger 0 arrives
A<> P1.Riding imply P1.Arrived // Passenger 1 arrives
A<> P2.Riding imply P2.Arrived // Passenger 2 arrives