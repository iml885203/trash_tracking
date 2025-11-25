# Core Package Refactoring Plan

## Objective
Improve core package architecture by addressing coupling issues, making state machine explicit, and reorganizing module structure while maintaining 100% backward compatibility and test coverage.

## Refactoring Strategy: TDD + Incremental

Each refactoring step follows TDD cycle:
1. **Red**: Write failing test for new behavior
2. **Green**: Implement minimum code to pass
3. **Refactor**: Clean up while keeping tests green
4. **Verify**: Run full test suite

## Phase 1: Foundation - Make State Machine Explicit

### Step 1.1: Fix PointMatcher API (use TruckState enum)
**Why**: Current `current_state: str = "idle"` is unsafe and has default value

**TDD Approach**:
- Write test expecting `TypeError` when passing string instead of enum
- Write test expecting `TypeError` when omitting current_state parameter
- Update existing tests to use `TruckState.IDLE` and `TruckState.NEARBY`

**Implementation**:
```python
# point_matcher.py
from trash_tracking_core.models.truck import TruckState

def check_line(self, truck_line: TruckLine, *, current_state: TruckState) -> MatchResult:
    """current_state is now keyword-only and required"""
```

**Files to change**:
- `packages/core/trash_tracking_core/core/point_matcher.py`
- `custom_components/trash_tracking/coordinator.py`
- `tests/core/test_point_matcher.py`
- `tests/core/test_tracker.py` (if needed)

**Risk**: Low - only API signature change
**Breaking Change**: Yes for external consumers (but we control all usage)

---

### Step 1.2: Simplify MatchResult to use Optional pattern
**Why**: `MatchResult(should_trigger=False)` is verbose, `Optional[StateTransition]` is more Pythonic

**TDD Approach**:
- Write tests expecting `None` when no transition
- Write tests expecting `StateTransition` object when transition occurs
- Verify caller code handles Optional correctly

**Implementation**:
```python
# point_matcher.py
@dataclass
class StateTransition:
    new_state: TruckState
    reason: str
    truck_line: TruckLine
    enter_point: Point
    exit_point: Point

def check_line(self, truck_line: TruckLine, *, current_state: TruckState) -> Optional[StateTransition]:
    if not enter_point or not exit_point:
        return None

    if current_state == TruckState.NEARBY and should_trigger_exit:
        return StateTransition(...)

    return None
```

**Files to change**:
- `packages/core/trash_tracking_core/core/point_matcher.py`
- `packages/core/trash_tracking_core/core/tracker.py`
- `custom_components/trash_tracking/coordinator.py`
- All test files using MatchResult

**Risk**: Medium - changes return type contract
**Breaking Change**: Yes

---

### Step 1.3: Create TrackingWindow value object
**Why**: enter_point + exit_point always appear together (data clump smell)

**TDD Approach**:
- Write test for TrackingWindow validation (same point, invalid order)
- Write test for TrackingWindow.find_points() returning None when points not found
- Write test for TrackingWindow.find_points() validating point order

**Implementation**:
```python
# models/tracking_window.py
@dataclass(frozen=True)
class TrackingWindow:
    enter_point_name: str
    exit_point_name: str

    def __post_init__(self):
        if self.enter_point_name == self.exit_point_name:
            raise ValueError("Enter and exit points must be different")

    def find_points(self, truck_line: TruckLine) -> Optional[tuple[Point, Point]]:
        enter = truck_line.find_point(self.enter_point_name)
        exit_pt = truck_line.find_point(self.exit_point_name)

        if not enter or not exit_pt:
            return None

        if exit_pt.point_rank <= enter.point_rank:
            raise ValueError(f"Exit point rank {exit_pt.point_rank} must be > enter point rank {enter.point_rank}")

        return (enter, exit_pt)
```

**Files to change**:
- Create `packages/core/trash_tracking_core/models/tracking_window.py`
- Update `core/point_matcher.py` to use TrackingWindow
- Update `core/state_manager.py`
- Update all configs and tests

**Risk**: Medium - new abstraction
**Breaking Change**: No (internal only)

---

## Phase 2: Decouple Components

### Step 2.1: Extract ResponseBuilder from StateManager
**Why**: StateManager shouldn't know about API response format (violates SRP)

**TDD Approach**:
- Write tests for ResponseBuilder.build_response() with various state scenarios
- Write tests verifying StateManager no longer has get_status_response()
- Update integration tests to use ResponseBuilder

**Implementation**:
```python
# core/response_builder.py
class StatusResponseBuilder:
    def build(self, state_manager: StateManager) -> dict[str, Any]:
        response = {
            "status": state_manager.current_state.value,
            "reason": state_manager.reason,
            "truck": None,
            "timestamp": state_manager.last_update.isoformat() if state_manager.last_update else None,
        }

        if state_manager.current_truck and state_manager.is_nearby():
            response["truck"] = self._serialize_truck(state_manager)

        return response
```

**Files to change**:
- Create `packages/core/trash_tracking_core/core/response_builder.py`
- Remove `get_status_response()` from `core/state_manager.py`
- Update `core/tracker.py` to use ResponseBuilder
- Update `custom_components/trash_tracking/coordinator.py`
- Update tests

**Risk**: Low - clear separation
**Breaking Change**: Yes for direct StateManager users

---

### Step 2.2: Create explicit StateMachine class
**Why**: State transition logic currently scattered across PointMatcher and StateManager

**TDD Approach**:
- Write tests for all state transitions (idle→nearby, nearby→idle)
- Write tests for invalid transitions (nearby→nearby)
- Write tests verifying state machine encapsulates transition rules

**Implementation**:
```python
# core/state_machine.py
class TruckStateMachine:
    def __init__(self, tracking_window: TrackingWindow):
        self.tracking_window = tracking_window

    def evaluate_transition(
        self,
        current_state: TruckState,
        truck_line: TruckLine
    ) -> Optional[StateTransition]:
        points = self.tracking_window.find_points(truck_line)
        if not points:
            return None

        enter_point, exit_point = points

        if current_state == TruckState.IDLE:
            if enter_point.has_passed():
                return StateTransition(
                    new_state=TruckState.NEARBY,
                    reason=f"Truck arrived at {enter_point.point_name}",
                    truck_line=truck_line,
                    enter_point=enter_point,
                    exit_point=exit_point,
                )

        elif current_state == TruckState.NEARBY:
            if exit_point.has_passed() or truck_line.arrival_rank >= exit_point.point_rank:
                return StateTransition(
                    new_state=TruckState.IDLE,
                    reason=f"Truck passed {exit_point.point_name}",
                    truck_line=truck_line,
                    enter_point=enter_point,
                    exit_point=exit_point,
                )

        return None
```

**Files to change**:
- Create `packages/core/trash_tracking_core/core/state_machine.py`
- Deprecate `core/point_matcher.py` (or simplify to just point finding)
- Update `core/tracker.py` to use StateMachine
- Update coordinator
- Create comprehensive tests

**Risk**: Medium-High - major restructuring
**Breaking Change**: Yes

---

## Phase 3: Reorganize and Polish

### Step 3.1: Reorganize module structure
**Why**: utils/ contains disparate concerns

**No TDD needed** (just moving files):

```bash
# Move geocoding to clients
mv packages/core/trash_tracking_core/utils/geocoding.py packages/core/trash_tracking_core/clients/

# Move route_analyzer to core
mv packages/core/trash_tracking_core/utils/route_analyzer.py packages/core/trash_tracking_core/core/

# Move config to dedicated module
mkdir packages/core/trash_tracking_core/config
mv packages/core/trash_tracking_core/utils/config.py packages/core/trash_tracking_core/config/config_manager.py
```

**Files to change**:
- Update all imports in core package
- Update imports in custom_components
- Update imports in tests
- Update __init__.py files

**Risk**: Low - mechanical refactoring
**Breaking Change**: Yes for import paths

---

### Step 3.2: Split ConfigManager into loader + validator + typed config
**Why**: ConfigManager mixes I/O, validation, and data access

**TDD Approach**:
- Write tests for TrackingConfig dataclass validation
- Write tests for YamlConfigLoader
- Write tests for ConfigValidator
- Ensure backward compatibility with existing tests

**Implementation**:
```python
# config/schemas.py
@dataclass
class Location:
    lat: float
    lng: float

@dataclass
class TrackingSettings:
    enter_point: str
    exit_point: str
    target_lines: List[str] = field(default_factory=list)

@dataclass
class ApiSettings:
    base_url: str
    timeout: int

@dataclass
class TrackingConfig:
    location: Location
    tracking: TrackingSettings
    api: ApiSettings

# config/loader.py
class YamlConfigLoader:
    def load(self, path: Path) -> TrackingConfig:
        ...

# config/validator.py
class ConfigValidator:
    def validate(self, config: TrackingConfig) -> List[str]:
        ...
```

**Files to change**:
- Create new config/ module files
- Update core/tracker.py to use new config types
- Update tests
- Keep old ConfigManager as deprecated wrapper for backward compat

**Risk**: Medium - complex refactoring
**Breaking Change**: Yes if removing old ConfigManager

---

### Step 3.3: Extract serialization from models
**Why**: Point.to_dict() and TruckLine.to_dict() contain presentation logic

**TDD Approach**:
- Write tests for TruckSerializer.serialize()
- Write tests for PointSerializer.serialize()
- Verify serialized output matches current format exactly

**Implementation**:
```python
# serializers/truck_serializer.py
class TruckSerializer:
    @staticmethod
    def serialize(
        truck: TruckLine,
        enter_point: Optional[Point] = None,
        exit_point: Optional[Point] = None
    ) -> dict:
        ...
```

**Files to change**:
- Create `packages/core/trash_tracking_core/serializers/`
- Move serialization logic from models
- Update StateManager/ResponseBuilder to use serializers
- Update tests

**Risk**: Low - isolated change
**Breaking Change**: No if keeping old methods

---

## Execution Order

### Recommended: Incremental Approach

**Phase 1A: Quick wins (Do Now)**
1. Fix PointMatcher API (current_state enum + keyword-only)
2. Create TrackingWindow value object

**Phase 1B: After beta testing**
3. Extract ResponseBuilder
4. Create explicit StateMachine

**Phase 2: Future release**
5. Reorganize module structure
6. Split ConfigManager
7. Extract serializers

### Alternative: Big Bang Approach (Not Recommended)

Do all refactoring at once. Risk: Too many changes, harder to debug if something breaks.

---

## Test Strategy

### Existing Tests (Keep Green)
- 222 unit tests must pass throughout
- BDD scenarios must pass
- No test should be deleted (only updated)

### New Tests to Write

**Phase 1A**:
- `test_point_matcher_state_enum.py` - Test TruckState enum validation
- `test_tracking_window.py` - Test TrackingWindow validation and find_points()

**Phase 1B**:
- `test_response_builder.py` - Test response building in isolation
- `test_state_machine.py` - Test explicit state machine transitions

**Phase 2**:
- `test_config_schema.py` - Test typed config validation
- `test_serializers.py` - Test model serialization

### Integration Tests
- Update BDD scenarios if any config flow changes
- Add scenario for state transition (idle→nearby→idle)

---

## Risk Mitigation

1. **Backward Compatibility**: Keep old APIs as deprecated wrappers during transition
2. **Incremental Commits**: Each step is a separate commit that can be reverted
3. **Feature Flag**: Add `USE_NEW_STATE_MACHINE` config flag for gradual rollout
4. **Rollback Plan**: Git tags at each phase for easy rollback

---

## Acceptance Criteria

### Must Have ✓
- All 222+ existing tests pass
- BDD scenarios pass
- Home Assistant integration works
- No performance regression

### Should Have ✓
- Code coverage remains >80%
- Mypy type checking passes with no errors
- Flake8 linting passes

### Nice to Have ⚙
- Improved test execution time
- Better error messages
- More comprehensive state machine tests

---

## Timeline Estimate

- **Phase 1A** (Quick wins): 2-4 hours
- **Phase 1B** (Decouple components): 3-5 hours
- **Phase 2** (Reorganize): 4-6 hours
- **Total**: 9-15 hours of development time

---

## Decision Points

Before starting, decide:

1. **Scope**: Do all phases or just Phase 1A?
2. **Breaking Changes**: Keep backward compatibility or clean break?
3. **Beta Testing**: Release beta between phases or after all phases?
4. **Config Migration**: Provide migration script for old config.yaml files?

---

## Rollback Strategy

If refactoring causes issues:

1. **Immediate**: `git revert HEAD` for last commit
2. **Phase-level**: `git reset --hard <phase_start_tag>`
3. **Full rollback**: `git revert <refactoring_start>..<refactoring_end>`

Tag commits for easy navigation:
- `refactor-phase-1a-start`
- `refactor-phase-1a-done`
- `refactor-phase-1b-start`
- etc.
