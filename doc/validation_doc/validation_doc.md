

## Risk Management

### General System Risks:
- Passenger's call up/down are not properly responded
- Passenger can't eventually reach their target floor
- Elevator goes out of normal range (floor -1 to 3)

### FTA Aanalysis
The detailed FTA result is given in the following diagram: 
<div align=center>
<img src="./imgs/FTA.png" width="500"/>
</div>

### UPPAAL model checking 

#### 1. Single Passenger
- This section will introduce a UPPAAL model which simulates the state machine in the situation of one passenger and one elevator. All the above risks will be tested by queries