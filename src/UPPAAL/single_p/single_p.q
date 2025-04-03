//This file was generated from (Academic) UPPAAL 5.0.0 (rev. 714BA9DB36F49691), 2023-06-21

/*
every call is eventually serviced
*/
A<> (callPlacedUp || callPlacedDown) imply (El.moving == true)

/*
Elevator always goes within floor -1 to 3
*/
A[] (El.c_floor >= MIN_FLOOR && El.c_floor <= MAX_FLOOR)

/*
passenger eventually reaches the floor
*/
A<> (P.Riding) imply (P.Arrived)
