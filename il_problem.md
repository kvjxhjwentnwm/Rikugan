# IL Optimizer — Design Problem

## What exists

`install_il_optimizer`, `remove_il_optimizer`, and `list_il_optimizers` in `rikugan/binja/tools/il.py` mirror the IDA microcode optimizer tools (`install_microcode_optimizer`, etc.) but are essentially dead code.

The tools compile and store a user-defined `optimize` function in an in-memory `installed_optimizers` dict. That function is **never called anywhere** — not by Rikugan, not by Binary Ninja.

## Why IDA's version works

IDA's Hex-Rays exposes a real optimizer plugin API:
- `install_optinsn_handler(optinsn_t*)` — hook called per microcode instruction during optimization passes
- `install_optblock_handler(optblock_t*)` — hook called per basic block

When registered, Hex-Rays calls these handlers automatically as part of its internal optimization pipeline every time a function is (re)decompiled. The optimizer runs transparently, inside the engine.

## Why Binary Ninja's version doesn't

Binary Ninja has no equivalent public hook for IL-level optimization passes. There is no `install_il_optimizer_handler()` API. BN's analysis pipeline is not extensible at the IL optimizer level from Python plugins.

The only ways to modify IL in BN from a plugin are:
- Write raw bytes via `bv.write()` or `bv.convert_to_nop()` and trigger re-analysis
- Use `BinaryView.add_analysis_completion_event()` to run code after analysis, but this is a one-shot callback, not a repeating optimizer hook
- Register a full `Architecture` or `Platform` plugin, which is far outside the scope of a per-function optimizer

## What the current tools actually do

- `install_il_optimizer` — compiles the Python code and stores it. Nothing else.
- `remove_il_optimizer` — deletes it from the dict.
- `list_il_optimizers` — lists stored entries.
- `redecompile_function` — shows the list of "active" optimizers as a status line but does not invoke any of them.

The optimizer concept has no dispatch path. An agent calling these tools would be misled into thinking patterns are being applied when they are not.

## What a real solution needs

A proper implementation requires deciding between two approaches:

**Option A — Explicit dispatch tool**
Add a `run_il_optimizer(name, func_address, level)` tool that walks the function's IL basic blocks and calls the stored `optimize_fn` per instruction/block. The optimizer would need `BinaryView` in scope to actually patch bytes. This is serviceable but loses the "transparent, always-on" behavior that makes IDA's version useful for deobfuscation workflows.

**Option B — Analysis completion hook**
Use `bv.add_analysis_completion_event()` or a `BackgroundTaskThread` to re-run registered optimizers whenever BN finishes analysis on a function. This is closer to IDA's pipeline integration but requires careful lifecycle management and may not re-trigger on the right granularity (BN's completion events are BinaryView-wide, not per-function).

**Option C — Remove the three optimizer tools**
Accept that this feature doesn't map to BN's architecture and remove `install_il_optimizer`, `remove_il_optimizer`, and `list_il_optimizers`. The `nop_instructions` tool plus `execute_python` already cover the actual patching use cases. The optimizer abstraction adds confusion without benefit until a real dispatch mechanism exists.

## Current status

The tools are left in place as stubs pending a design decision. They do not break anything — they just don't do what they imply. `il_problem.md` (this file) tracks the issue.
