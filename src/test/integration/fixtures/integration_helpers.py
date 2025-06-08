"""
Integration test helper utilities.
Provides common utilities and helper functions for integration tests.
"""

import time
import threading
from typing import Callable, Any, Dict, List
from backend.models import ElevatorState, DoorState, MIN_FLOOR, MAX_FLOOR


class TestScenarioBuilder:
    """Helper for building complex test scenarios."""
    
    def __init__(self, system_harness):
        self.harness = system_harness
        self.scenario_steps = []
        
    def add_call(self, floor: int, direction: str, delay: float = 0):
        """Add a call step to the scenario."""
        self.scenario_steps.append({
            'type': 'call',
            'floor': floor,
            'direction': direction,
            'delay': delay
        })
        return self
    
    def add_floor_selection(self, elevator_id: int, floor: int, delay: float = 0):
        """Add a floor selection step to the scenario."""
        self.scenario_steps.append({
            'type': 'select_floor',
            'elevator_id': elevator_id,
            'floor': floor,
            'delay': delay
        })
        return self
    
    def add_door_operation(self, elevator_id: int, operation: str, delay: float = 0):
        """Add a door operation step to the scenario."""
        self.scenario_steps.append({
            'type': 'door_operation',
            'elevator_id': elevator_id,
            'operation': operation,  # 'open' or 'close'
            'delay': delay
        })
        return self
    
    def add_wait(self, duration: float):
        """Add a wait step to the scenario."""
        self.scenario_steps.append({
            'type': 'wait',
            'duration': duration
        })
        return self
    
    def execute(self, simulate_time_func):
        """Execute the built scenario."""
        results = []
        
        for step in self.scenario_steps:
            if step['delay'] > 0:
                simulate_time_func(self.harness.system, step['delay'])
            
            if step['type'] == 'call':
                result = self.harness.send_call(step['floor'], step['direction'])
                results.append(('call', result))
                
            elif step['type'] == 'select_floor':
                result = self.harness.select_floor(step['elevator_id'], step['floor'])
                results.append(('select_floor', result))
                
            elif step['type'] == 'door_operation':
                if step['operation'] == 'open':
                    result = self.harness.open_door(step['elevator_id'])
                else:
                    result = self.harness.close_door(step['elevator_id'])
                results.append(('door_operation', result))
                
            elif step['type'] == 'wait':
                simulate_time_func(self.harness.system, step['duration'])
                results.append(('wait', True))
        
        return results


class PerformanceMonitor:
    """Monitor performance metrics during integration tests."""
    
    def __init__(self):
        self.metrics = {
            'response_times': [],
            'state_changes': [],
            'message_counts': {'zmq': 0, 'websocket': 0},
            'error_counts': 0,
            'start_time': None
        }
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.metrics['start_time'] = time.time()
    
    def record_response_time(self, operation: str, duration: float):
        """Record response time for an operation."""
        self.metrics['response_times'].append({
            'operation': operation,
            'duration': duration,
            'timestamp': time.time()
        })
    
    def record_state_change(self, component: str, old_state: Any, new_state: Any):
        """Record a state change."""
        self.metrics['state_changes'].append({
            'component': component,
            'old_state': str(old_state),
            'new_state': str(new_state),
            'timestamp': time.time()
        })
    
    def record_message(self, channel: str):
        """Record a message sent."""
        if channel in self.metrics['message_counts']:
            self.metrics['message_counts'][channel] += 1
    
    def record_error(self):
        """Record an error occurrence."""
        self.metrics['error_counts'] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if self.metrics['start_time']:
            total_time = time.time() - self.metrics['start_time']
        else:
            total_time = 0
        
        response_times = [rt['duration'] for rt in self.metrics['response_times']]
        
        return {
            'total_time': total_time,
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'state_change_count': len(self.metrics['state_changes']),
            'total_messages': sum(self.metrics['message_counts'].values()),
            'error_count': self.metrics['error_counts'],
            'messages_per_second': sum(self.metrics['message_counts'].values()) / total_time if total_time > 0 else 0
        }


class StateValidator:
    """Validate system state consistency."""
    
    @staticmethod
    def validate_elevator_state(elevator_state: Dict[str, Any]) -> List[str]:
        """Validate elevator state and return list of errors."""
        errors = []
        
        # Validate floor range
        if not (MIN_FLOOR <= elevator_state['floor'] <= MAX_FLOOR):
            errors.append(f"Floor {elevator_state['floor']} out of valid range")
        
        # Validate elevator state
        if elevator_state['state'] not in [ElevatorState.IDLE, ElevatorState.MOVING_UP, ElevatorState.MOVING_DOWN]:
            errors.append(f"Invalid elevator state: {elevator_state['state']}")
        
        # Validate door state
        if elevator_state['door_state'] not in [DoorState.OPEN, DoorState.CLOSED, DoorState.OPENING, DoorState.CLOSING]:
            errors.append(f"Invalid door state: {elevator_state['door_state']}")
        
        # Validate movement with doors
        if (elevator_state['state'] in [ElevatorState.MOVING_UP, ElevatorState.MOVING_DOWN] and
            elevator_state['door_state'] != DoorState.CLOSED):
            errors.append("Elevator moving with doors not closed")
        
        # Validate task queue
        for task in elevator_state.get('task_queue', []):
            if hasattr(task, 'floor') and not (MIN_FLOOR <= task.floor <= MAX_FLOOR):
                errors.append(f"Task floor {task.floor} out of valid range")
        
        return errors
    
    @staticmethod
    def validate_system_state(system_state: Dict[str, Any]) -> List[str]:
        """Validate complete system state."""
        errors = []
        
        # Validate each elevator
        for i, elevator_state in enumerate(system_state.get('elevators', [])):
            elevator_errors = StateValidator.validate_elevator_state(elevator_state)
            for error in elevator_errors:
                errors.append(f"Elevator {i + 1}: {error}")
        
        # Validate pending calls count
        pending_calls = system_state.get('pending_calls', 0)
        if pending_calls < 0:
            errors.append(f"Invalid pending calls count: {pending_calls}")
        
        # Validate elapsed time
        elapsed_time = system_state.get('elapsed_time', 0)
        if elapsed_time < 0:
            errors.append(f"Invalid elapsed time: {elapsed_time}")
        
        return errors


class ConcurrencyTester:
    """Helper for testing concurrent operations."""
    
    def __init__(self, system_harness):
        self.harness = system_harness
        self.results = []
        self.errors = []
    
    def run_concurrent_operations(self, operations: List[Callable], max_workers: int = 5):
        """Run multiple operations concurrently."""
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all operations
            futures = [executor.submit(op) for op in operations]
            
            # Collect results
            for future in concurrent.futures.as_completed(futures, timeout=10):
                try:
                    result = future.result()
                    self.results.append(result)
                except Exception as e:
                    self.errors.append(e)
    
    def create_call_operation(self, floor: int, direction: str):
        """Create a call operation function."""
        def operation():
            return self.harness.send_call(floor, direction)
        return operation
    
    def create_floor_select_operation(self, elevator_id: int, floor: int):
        """Create a floor selection operation function."""
        def operation():
            return self.harness.select_floor(elevator_id, floor)
        return operation
    
    def create_door_operation(self, elevator_id: int, operation_type: str):
        """Create a door operation function."""
        def operation():
            if operation_type == 'open':
                return self.harness.open_door(elevator_id)
            else:
                return self.harness.close_door(elevator_id)
        return operation
    
    def get_success_rate(self) -> float:
        """Get success rate of operations."""
        if not self.results:
            return 0.0
        
        successful = sum(1 for result in self.results if result)
        return successful / len(self.results)
    
    def get_error_rate(self) -> float:
        """Get error rate of operations."""
        total_operations = len(self.results) + len(self.errors)
        if total_operations == 0:
            return 0.0
        
        return len(self.errors) / total_operations


class LoadTestGenerator:
    """Generate load test scenarios."""
    
    @staticmethod
    def generate_realistic_usage_pattern():
        """Generate a realistic elevator usage pattern."""
        scenarios = []
        
        # Morning rush - people going up
        for _ in range(10):
            scenarios.append(('call', 1, 'up'))
            scenarios.append(('select_floor', 1, 3))
        
        # Midday traffic - mixed directions
        for floor in [1, 2, 3]:
            scenarios.append(('call', floor, 'up'))
            scenarios.append(('call', floor, 'down'))
        
        # Evening rush - people going down
        for _ in range(8):
            scenarios.append(('call', 3, 'down'))
            scenarios.append(('select_floor', 1, 1))
        
        return scenarios
    
    @staticmethod
    def generate_stress_test_pattern():
        """Generate a stress test pattern."""
        scenarios = []
        
        # Rapid calls from all floors
        for _ in range(20):
            for floor in [1, 2, 3]:
                for direction in ['up', 'down']:
                    if (floor == MAX_FLOOR and direction == 'up') or (floor == MIN_FLOOR and direction == 'down'):
                        continue
                    scenarios.append(('call', floor, direction))
        
        # Rapid floor selections
        for _ in range(15):
            for elevator_id in [1, 2]:
                for floor in [1, 2, 3]:
                    scenarios.append(('select_floor', elevator_id, floor))
        
        return scenarios
    
    @staticmethod
    def generate_edge_case_pattern():
        """Generate edge case scenarios."""
        scenarios = []
        
        # Boundary floor operations
        scenarios.extend([
            ('call', MIN_FLOOR, 'up'),
            ('call', MAX_FLOOR, 'down'),
            ('select_floor', 1, MIN_FLOOR),
            ('select_floor', 2, MAX_FLOOR)
        ])
        
        # Rapid door operations
        for elevator_id in [1, 2]:
            for _ in range(5):
                scenarios.extend([
                    ('door_open', elevator_id, None),
                    ('door_close', elevator_id, None)
                ])
        
        return scenarios
