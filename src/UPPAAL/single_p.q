//This file was generated from (Academic) UPPAAL 5.0.0 (rev. 714BA9DB36F49691), 2023-06-21

/*
every call is eventually serviced
*/
A[] (callPlacedUp || callPlacedDown) imply (<> E.moving == true)

/*
goes within floor -1 to 3
*/
A[] (E.floor >= MIN_FLOOR && E.floor <= MAX_FLOOR)

/*
passenger eventually reaches the floor
*/
A[] (P.riding) --> (<> P.arrived)
