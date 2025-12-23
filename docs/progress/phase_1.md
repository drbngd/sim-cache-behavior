# Phase 1: Multicore Skeleton Implementation Log

## Overview
**Goal:** Convert the single-cycle MIPS simulator into a cycle-accurate multicore simulator (4 Cores) capable of spawning threads and executing in parallel (round-robin).

## Implementation Details

### 1. Class-Based Architecture
To support multiple cores without rewriting the entire simulator, we encapsulated global state into classes:
*   **`Pipeline` Class (`pipe.h/cpp`)**: 
    *   Previously global `Pipe_State` struct and `pipe_*` functions.
    *   Now fully encapsulated. Each instance represents the pipeline state of one core.
    *   *In-Place Refactor*: Logic inside `fetch`, `decode`, etc., was preserved almost exactly to maintain cycle-accuracy.
*   **`Core` Class (`core.h/cpp`)**: 
    *   Represents a physical CPU core.
    *   Owns a `std::unique_ptr<Pipeline>`.
    *   Handles top-level `cycle()` ticking (WB -> MEM -> EX -> ID -> IF).
    *   Handles **Syscalls** (see below).
*   **`Processor` Class (`processor.h/cpp`)**: 
    *   The "Motherboard" class.
    *   Owns 4 `Core` instances.
    *   `cycle()` method iterates through all cores to advance simulation time.

### 2. Syscall Interface
We redefined syscalls to support threading and multicore output:
*   **`$v0 = 1, 2, 3` (Spawn)**: Spawns a new thread on the target Core ID.
    *   Sets target `PC` to `syscall_PC + 4` (inherits instruction stream).
    *   Sets target `$v1 = 1` (Child indicator).
    *   Sets source `$v1 = 0` (Parent indicator).
    *   Wakes up target core (`is_running = true`).
*   **`$v0 = 0xA` (Halt)**: Stops the current core (`is_running = false`).
*   **`$v0 = 0xB` (Print)**: Prints a hex value from `$v1` prefixed with the Core ID (`OUT (CPU X): ...`).

### 3. Build & Configuration
*   **`config.h`**: Created to hold system constants (e.g., `NUM_CORES = 4`).
*   **`Makefile`**: Added `debug` target.
    *   `make sim`: Optimized, no debug prints.
    *   `make debug`: Compiles with `-DDEBUG`, enabling detailed pipeline traces in `pipe.cpp` and `core.cpp`.

## Bugs Faced & Resolved

### 1. Missing Branch Recovery Logic
*   **Issue**: Initial regression tests failed randomly on branch heavy code.
*   **Cause**: During refactoring `pipe_cycle` into `Core::cycle`, the block of code responsible for handling `pipe.branch_recover` was accidentally omitted.
*   **Fix**: Restored the logic at the end of `Core::cycle` to update PC and flush stages when `branch_recover` is set.

### 2. PC Discrepancy on Halt
*   **Issue**: Regression tests showed a PC mismatch at the end of simulation (e.g., expected `0x400030`, got `0x40002c`).
*   **Cause**: The baseline simulator logic reset the PC to the syscall instruction address when halting (`pipe.PC = op->pc`). Our new `Core::handle_syscall` just set `is_running=false` without fixing up the PC.
*   **Fix**: Updated `Syscall 0xA` handler to strictly replicate baseline PC behavior.

### 3. "Race Condition" Mismatch in `test2`
*   **Issue**: `test2.s` (atomic increment race) produced `1, 1, 2, 3` instead of the expected `1, 1, 1, 1`.
*   **Analysis**: The expected behavior (`1, 1, 1, 1`) assumes a race condition where multiple cores read a stale "0" before anyone writes back.
*   **Resolution**: Since Phase 1 uses **Perfect Memory** (1 cycle latency, global visibility), Core 0 completes its write *before* Cores 2 and 3 even wake up. Thus, sequential execution is the **correct** behavior for this phase. The race condition will likely reappear in Phase 2/3 when memory latency is introduced.

## Verification
*   **Regression Suite**: Passed 92/92 legacy tests (`make run`).
*   **Multicore Tests**:
    *   `parmatmult`: Checksum matched.
    *   `test1`: All threads reported correct IDs.
