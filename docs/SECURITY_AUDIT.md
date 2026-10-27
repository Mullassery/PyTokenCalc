# Security Vulnerability Audit - PyTokenCalc

**Audit Date:** 2026-10-27
**Repository:** /Users/georgimullassery/Desktop/Projects/PyTokenCalc
**Total Findings:** 253

## Summary
- **Critical:** 183
- **Medium:** 70

## Findings

### 1. [Critical] Command Injection
- **File:** .claude/settings.json:12
- **Description:** os.system()
- **Evidence (Line):** `"command": "python3 -c \"import json,sys,os; data=json.load(sys.stdin); cmd=data.get('tool_name','un`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 2. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_code/code.py:164
- **Description:** eval()
- **Evidence (Line):** `def eval(self, code, **vars):`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 3. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_code/code.py:173
- **Description:** eval()
- **Evidence (Line):** `return eval(code, self.f_globals, f_locals)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 4. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_code/code.py:326
- **Description:** eval()
- **Evidence (Line):** `# however via `exec(...)` / `eval(...)` they can be other types`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 5. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_code/code.py:326
- **Description:** exec()
- **Evidence (Line):** `# however via `exec(...)` / `eval(...)` they can be other types`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 6. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_py/path.py:1153
- **Description:** exec()
- **Evidence (Line):** `exec(f.read(), mod.__dict__)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 7. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/_py/path.py:1159
- **Description:** exec()
- **Evidence (Line):** `def sysexec(self, *argv: os.PathLike[str], **popen_opts: Any) -> str:`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 8. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/assertion/rewrite.py:188
- **Description:** exec()
- **Evidence (Line):** `exec(co, module.__dict__)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 9. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/assertion/rewrite.py:393
- **Description:** marshal load
- **Evidence (Line):** `co = marshal.load(fp)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 10. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/capture.py:1112
- **Description:** os.system()
- **Evidence (Line):** `os.system('echo "hello"')`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 11. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/capture.py:1140
- **Description:** os.system()
- **Evidence (Line):** `os.system('echo "hello"')`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 12. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/mark/__init__.py:66
- **Description:** eval()
- **Evidence (Line):** `def test_eval(test_input, expected):`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 13. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/mark/__init__.py:67
- **Description:** eval()
- **Evidence (Line):** `assert eval(test_input) == expected`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 14. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/mark/expression.py:295
- **Description:** eval()
- **Evidence (Line):** `"""Adapts a matcher function to a locals mapping as required by eval()."""`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 15. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/mark/expression.py:353
- **Description:** eval()
- **Evidence (Line):** `return bool(eval(self._code, {"__builtins__": {}}, MatcherAdapter(matcher)))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 16. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/pytester.py:296
- **Description:** eval()
- **Evidence (Line):** `if eval(check, backlocals, call.__dict__):`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 17. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/skipping.py:92
- **Description:** eval()
- **Evidence (Line):** `If an old-style string condition is given, it is eval()'d, otherwise the`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 18. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/_pytest/skipping.py:119
- **Description:** eval()
- **Evidence (Line):** `result = eval(condition_code, globals_)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 19. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/anyio/_backends/_asyncio.py:2796
- **Description:** exec()
- **Evidence (Line):** `# Use loop.subprocess_shell()/subprocess_exec() rather than their`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 20. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/anyio/_backends/_asyncio.py:2810
- **Description:** exec()
- **Evidence (Line):** `transport, protocol = await loop.subprocess_exec(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 21. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/anyio/to_interpreter.py:123
- **Description:** exec()
- **Evidence (Line):** `exc_info = _interpreters.exec(self._interpreter_id, _run_func)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 22. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/anyio/to_interpreter.py:130
- **Description:** pickle load/dumps
- **Evidence (Line):** `res = pickle.loads(res)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 23. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/anyio/to_process.py:95
- **Description:** pickle load/dumps
- **Evidence (Line):** `retval = pickle.loads(pickled_response)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 24. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/anyio/to_process.py:220
- **Description:** pickle load/dumps
- **Evidence (Line):** `command, *args = pickle.load(stdin.buffer)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 25. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/attr/_make.py:216
- **Description:** eval()
- **Evidence (Line):** `def _compile_and_eval(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 26. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/attr/_make.py:227
- **Description:** eval()
- **Evidence (Line):** `eval(bytecode, globs, locs)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 27. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/attr/_make.py:260
- **Description:** eval()
- **Evidence (Line):** `_compile_and_eval(script, globs, locs, filename)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 28. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/attr/_make.py:1690
- **Description:** eval()
- **Evidence (Line):** `_compile_and_eval(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 29. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/attr/_make.py:1810
- **Description:** eval()
- **Evidence (Line):** `_compile_and_eval(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 30. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/attr/_make.py:1884
- **Description:** eval()
- **Evidence (Line):** `_compile_and_eval(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 31. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/code/__init__.py:2708
- **Description:** eval()
- **Evidence (Line):** `#            BeartypeConfigDecor = eval(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 32. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/code/__init__.py:1963
- **Description:** exec()
- **Evidence (Line):** `#        s = await asyncio.create_subprocess_exec("ls", loop=event_loop)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 33. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/forward/fwdresolve.py:316
- **Description:** eval()
- **Evidence (Line):** `# nothing" call of the low-level eval() builtin accepting *NO*`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 34. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/forward/fwdresolve.py:410
- **Description:** eval()
- **Evidence (Line):** `# require dynamic evaluation under the eval() builtin. Why? Because this`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 35. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/forward/fwdresolve.py:541
- **Description:** eval()
- **Evidence (Line):** `hint_resolved = eval(hint, scope_forward)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 36. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/forward/scope/fwdscopecls.py:354
- **Description:** eval()
- **Evidence (Line):** `# however via `exec(...)` / `eval(...)` they can be other types`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 37. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/forward/scope/fwdscopecls.py:469
- **Description:** eval()
- **Evidence (Line):** `# A call to the eval() or exec() builtin.`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 38. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/forward/scope/fwdscopecls.py:471
- **Description:** eval()
- **Evidence (Line):** `# Note that calls to the eval() or exec() builtin that originate`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 39. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/forward/scope/fwdscopecls.py:473
- **Description:** eval()
- **Evidence (Line):** `# from calls to the eval() or exec() builtin that originate from`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 40. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/forward/scope/fwdscopecls.py:476
- **Description:** eval()
- **Evidence (Line):** `# this caller is a call to the eval() or exec() builtin).`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 41. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/forward/scope/fwdscopecls.py:480
- **Description:** eval()
- **Evidence (Line):** `# _resolve_hint_pep484_ref_str() function calls the eval()`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 42. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/forward/scope/fwdscopecls.py:483
- **Description:** eval()
- **Evidence (Line):** `#     # This is the eval() call triggering this call.`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 43. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/forward/scope/fwdscopecls.py:484
- **Description:** eval()
- **Evidence (Line):** `#     hint_resolved = eval(hint, scope_forward)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 44. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/forward/scope/fwdscopecls.py:485
- **Description:** eval()
- **Evidence (Line):** `is_frame_eval(frame_caller)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 45. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/forward/scope/fwdscopecls.py:354
- **Description:** exec()
- **Evidence (Line):** `# however via `exec(...)` / `eval(...)` they can be other types`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 46. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/forward/scope/fwdscopecls.py:469
- **Description:** exec()
- **Evidence (Line):** `# A call to the eval() or exec() builtin.`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 47. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/forward/scope/fwdscopecls.py:471
- **Description:** exec()
- **Evidence (Line):** `# Note that calls to the eval() or exec() builtin that originate`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 48. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/forward/scope/fwdscopecls.py:473
- **Description:** exec()
- **Evidence (Line):** `# from calls to the eval() or exec() builtin that originate from`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 49. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_check/forward/scope/fwdscopecls.py:476
- **Description:** exec()
- **Evidence (Line):** `# this caller is a call to the eval() or exec() builtin).`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 50. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_decor/_nontype/_wrap/__init__.py:360
- **Description:** eval()
- **Evidence (Line):** `#* Evaluate that code object by calling either the exec() or eval() builtin to`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 51. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_decor/_nontype/_wrap/__init__.py:54
- **Description:** exec()
- **Evidence (Line):** `#    probably want to stop passing "globals()" to exec() below and instead pass`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 52. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_decor/_nontype/_wrap/__init__.py:360
- **Description:** exec()
- **Evidence (Line):** `#* Evaluate that code object by calling either the exec() or eval() builtin to`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 53. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_decor/_nontype/_wrap/wrapmain.py:86
- **Description:** exec()
- **Evidence (Line):** `(presumably, a subtle bug in the exec() builtin), this is *not*`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 54. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_decor/_nontype/decornontype.py:512
- **Description:** eval()
- **Evidence (Line):** `#   *ALL* pure-Python code snippets dynamically executed by the eval() and`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 55. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_decor/_nontype/decornontype.py:513
- **Description:** exec()
- **Evidence (Line):** `#   exec() builtins should *ALWAYS* have implicit access to builtin`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 56. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/cache/func/utilcacheproperty.py:16
- **Description:** exec()
- **Evidence (Line):** `# Global attributes implicitly required by the exec() call internally performed`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 57. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/cache/func/utilcacheproperty.py:137
- **Description:** exec()
- **Evidence (Line):** `exec(func_body, globals(), local_attrs)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 58. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:134
- **Description:** eval()
- **Evidence (Line):** `def is_frame_eval(frame: CallableFrameType) -> bool:`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 59. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:167
- **Description:** eval()
- **Evidence (Line):** `#for scopes that are *NOT* eval() or exec() calls. No idea, honestly. *sigh*`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 60. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:173
- **Description:** eval()
- **Evidence (Line):** `# objects underlying both pure-Python modules (as well as all eval() and`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 61. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:178
- **Description:** eval()
- **Evidence (Line):** `# underlying all eval() or exec() calls.`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 62. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:222
- **Description:** eval()
- **Evidence (Line):** `# objects underlying both pure-Python modules (as well as all eval() and`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 63. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:227
- **Description:** eval()
- **Evidence (Line):** `# objects underlying all eval() or exec() calls.`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 64. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:577
- **Description:** eval()
- **Evidence (Line):** `# the enclosing class or module before eval() is called. See also:`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 65. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:795
- **Description:** eval()
- **Evidence (Line):** `# This frame encapsulates an eval() or exec() call...`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 66. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:797
- **Description:** eval()
- **Evidence (Line):** `# Note that eval() and exec() calls do *NOT* constitute pure-Python`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 67. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:800
- **Description:** eval()
- **Evidence (Line):** `is_frame_eval(frame)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 68. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:803
- **Description:** eval()
- **Evidence (Line):** `# an eval() or exec() call. In this case...`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 69. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:167
- **Description:** exec()
- **Evidence (Line):** `#for scopes that are *NOT* eval() or exec() calls. No idea, honestly. *sigh*`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 70. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:174
- **Description:** exec()
- **Evidence (Line):** `# exec() calls) *AND*...`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 71. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:178
- **Description:** exec()
- **Evidence (Line):** `# underlying all eval() or exec() calls.`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 72. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:223
- **Description:** exec()
- **Evidence (Line):** `# exec() calls) *AND*...`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 73. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:227
- **Description:** exec()
- **Evidence (Line):** `# objects underlying all eval() or exec() calls.`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 74. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:795
- **Description:** exec()
- **Evidence (Line):** `# This frame encapsulates an eval() or exec() call...`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 75. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:797
- **Description:** exec()
- **Evidence (Line):** `# Note that eval() and exec() calls do *NOT* constitute pure-Python`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 76. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncframe.py:803
- **Description:** exec()
- **Evidence (Line):** `# an eval() or exec() call. In this case...`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 77. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncmake.py:261
- **Description:** exec()
- **Evidence (Line):** `# simply calling "exec(func_code, func_globals, func_locals)". Why?`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 78. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncmake.py:262
- **Description:** exec()
- **Evidence (Line):** `# Because the exec() builtin does *NOT* provide a means to set this`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 79. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/func/utilfuncmake.py:276
- **Description:** exec()
- **Evidence (Line):** `exec(func_code_compiled, func_globals, func_locals)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 80. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/hint/pep/proposal/pep613.py:111
- **Description:** exec()
- **Evidence (Line):** `f'        exec("type alias_name = alias_value")  # <-- eldritch abomination\n'`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 81. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/hint/pep/proposal/pep695.py:72
- **Description:** exec()
- **Evidence (Line):** `#        # non-exec()-based solution. Note that this optimization does *NOT*`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 82. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/hint/pep/proposal/pep695.py:79
- **Description:** exec()
- **Evidence (Line):** `#        # fallback to an inefficient exec()-based solution.`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 83. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/_util/hint/pep/proposal/pep695.py:81
- **Description:** exec()
- **Evidence (Line):** `#            exec(f'{__hint_pep695_forwardref_beartype__.__hint_name_beartype__} = __hint_pep695_for`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 84. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/beartype/claw/_ast/_pep/clawastpep695.py:251
- **Description:** exec()
- **Evidence (Line):** `#         exec(f'{_.__hint_name_beartype__} = _')`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 85. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/cffi/_cffi_gen_src.py:53
- **Description:** exec()
- **Evidence (Line):** `exec(compiled, globs, globs)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 86. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/cffi/recompiler.py:80
- **Description:** eval()
- **Evidence (Line):** `flags = eval(self.flags, G_FLAGS)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 87. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/cffi/setuptools_ext.py:26
- **Description:** exec()
- **Evidence (Line):** `exec(code, glob, glob)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 88. [Critical] Hardcoded Secret
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/hazmat/_oid.py:372
- **Description:** Password Assignment detected
- **Evidence (Line):** `AttributeOID.CHALLENGE_PASSWORD: "challengePassword",`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 89. [Critical] Hardcoded Secret
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/hazmat/primitives/serialization/ssh.py:77
- **Description:** Private Key detected
- **Evidence (Line):** `_SK_START = b"-----BEGIN OPENSSH PRIVATE KEY-----"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 90. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/fastmcp/cli/apps_dev.py:1742
- **Description:** exec()
- **Evidence (Line):** `process = await asyncio.create_subprocess_exec(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 91. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/fastmcp/cli/run.py:423
- **Description:** exec()
- **Evidence (Line):** `process = await asyncio.create_subprocess_exec(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 92. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/fastmcp/experimental/transforms/code_mode.py:143
- **Description:** exec()
- **Evidence (Line):** `sandbox — never with plain ``exec()``.  Use ``MontySandboxProvider```
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 93. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/fastmcp/server/providers/skills/_common.py:109
- **Description:** yaml.load (unsafe)
- **Evidence (Line):** `parsed = yaml.load(frontmatter_text, Loader=yaml.BaseLoader)  # noqa: S506`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 94. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/flask/cli.py:150
- **Description:** eval()
- **Evidence (Line):** `args = [ast.literal_eval(arg) for arg in expr.args]`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 95. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/flask/cli.py:152
- **Description:** eval()
- **Evidence (Line):** `kw.arg: ast.literal_eval(kw.value)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 96. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/flask/cli.py:1031
- **Description:** eval()
- **Evidence (Line):** `eval(compile(f.read(), startup, "exec"), ctx)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 97. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/flask/config.py:209
- **Description:** exec()
- **Evidence (Line):** `exec(compile(config_file.read(), filename, "exec"), d.__dict__)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 98. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/griffe/_internal/extensions/dataclasses.py:61
- **Description:** eval()
- **Evidence (Line):** `args.update({ast.literal_eval(str(key)): value for key, value in zip(expr.keys, expr.values, strict=`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 99. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/griffe/_internal/extensions/unpack_typeddict.py:90
- **Description:** eval()
- **Evidence (Line):** `total = ast.literal_eval(str(value))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 100. [Critical] Hardcoded Secret
- **File:** .venv-test/lib/python3.12/site-packages/httpx2/_urls.py:352
- **Description:** Password Assignment detected
- **Evidence (Line):** `username="jo@gmail.com", password="a secret"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 101. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/hypothesis/extra/_patching.py:94
- **Description:** eval()
- **Evidence (Line):** `lambda x: literal_eval(x.value) in strip_via`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 102. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/hypothesis/extra/ghostwriter.py:278
- **Description:** eval()
- **Evidence (Line):** `elements.append(ast.literal_eval(token))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 103. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/hypothesis/internal/filtering.py:96
- **Description:** eval()
- **Evidence (Line):** `return ast.literal_eval(node)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 104. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/hypothesis/internal/lambda_sources.py:265
- **Description:** eval()
- **Evidence (Line):** `compiled = eval(source, f_globals)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 105. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/hypothesis/internal/lambda_sources.py:298
- **Description:** exec()
- **Evidence (Line):** `exec(exec_str, f_globals)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 106. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/hypothesis/internal/reflection.py:367
- **Description:** exec()
- **Evidence (Line):** `exec(source, result.__dict__)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 107. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/jaraco/functools/__init__.py:592
- **Description:** eval()
- **Evidence (Line):** `return eval(use)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 108. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/bccache.py:73
- **Description:** pickle load/dumps
- **Evidence (Line):** `checksum = pickle.load(f)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 109. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/bccache.py:79
- **Description:** marshal load
- **Evidence (Line):** `self.code = marshal.load(f)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 110. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/debug.py:145
- **Description:** exec()
- **Evidence (Line):** `exec(code, globals, locals)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 111. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/environment.py:1228
- **Description:** exec()
- **Evidence (Line):** `exec(code, namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 112. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/lexer.py:663
- **Description:** eval()
- **Evidence (Line):** `value = literal_eval(value_str.replace("_", ""))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 113. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/nativetypes.py:40
- **Description:** eval()
- **Evidence (Line):** `return literal_eval(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 114. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/nodes.py:581
- **Description:** eval()
- **Evidence (Line):** `representation (objects where ``eval(repr(x)) == x`` is true).`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 115. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/jsonschema/tests/test_deprecations.py:396
- **Description:** eval()
- **Evidence (Line):** `def test_automatic_remote_retrieval(self):`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 116. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/key_value/aio/stores/s3/store.py:234
- **Description:** eval()
- **Evidence (Line):** `S3 object metadata and checked client-side during retrieval (S3 lifecycle policies`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 117. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/mcp/cli/cli.py:48
- **Description:** subprocess with shell=True
- **Evidence (Line):** `subprocess.run([cmd, "--version"], check=True, capture_output=True, shell=True)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 118. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/more_itertools/recipes.py:1106
- **Description:** eval()
- **Evidence (Line):** `def polynomial_eval(coefficients, x):`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 119. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/more_itertools/recipes.py:1115
- **Description:** eval()
- **Evidence (Line):** `>>> polynomial_eval(coefficients, x)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 120. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/packaging/_parser.py:397
- **Description:** eval()
- **Evidence (Line):** `value = ast.literal_eval(python_str)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 121. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/packaging/_structures.py:10
- **Description:** pickle load/dumps
- **Evidence (Line):** `stand-in classes so that ``pickle.loads()`` can resolve those references.`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 122. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_hooks.py:512
- **Description:** exec()
- **Evidence (Line):** `return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 123. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_hooks.py:534
- **Description:** exec()
- **Evidence (Line):** `res = self._hookexec(self.name, self._hookimpls.copy(), kwargs, False)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 124. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_hooks.py:573
- **Description:** exec()
- **Evidence (Line):** `return self._hookexec(self.name, hookimpls, kwargs, firstresult)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 125. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_hooks.py:580
- **Description:** exec()
- **Evidence (Line):** `res = self._hookexec(self.name, [method], kwargs, False)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 126. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_manager.py:111
- **Description:** exec()
- **Evidence (Line):** `def _hookexec(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 127. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_manager.py:120
- **Description:** exec()
- **Evidence (Line):** `return self._inner_hookexec(hook_name, methods, kwargs, firstresult)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 128. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pluggy/_manager.py:464
- **Description:** exec()
- **Evidence (Line):** `def traced_hookexec(`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 129. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_decorators.py:599
- **Description:** eval()
- **Evidence (Line):** `sig = signature_no_eval(validator)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 130. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_decorators.py:637
- **Description:** eval()
- **Evidence (Line):** `sig = signature_no_eval(serializer)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 131. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_decorators.py:675
- **Description:** eval()
- **Evidence (Line):** `sig = signature_no_eval(serializer)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 132. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_decorators.py:707
- **Description:** eval()
- **Evidence (Line):** `sig = signature_no_eval(serializer)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 133. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_decorators.py:755
- **Description:** eval()
- **Evidence (Line):** `sig = signature_no_eval(unwrap_wrapped_function(function))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 134. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_decorators.py:779
- **Description:** eval()
- **Evidence (Line):** `sig = signature_no_eval(unwrap_wrapped_function(function))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 135. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_fields.py:849
- **Description:** eval()
- **Evidence (Line):** `sig = _typing_extra.signature_no_eval(default_factory)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 136. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_generate_schema.py:2030
- **Description:** eval()
- **Evidence (Line):** `sig = _typing_extra.signature_no_eval(function)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 137. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_generate_schema.py:2055
- **Description:** eval()
- **Evidence (Line):** `sig = _typing_extra.signature_no_eval(function)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 138. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_generate_schema.py:2134
- **Description:** eval()
- **Evidence (Line):** `sig = _typing_extra.signature_no_eval(function)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 139. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_namespace_utils.py:38
- **Description:** eval()
- **Evidence (Line):** `return eval(typ, *ns)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 140. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_signature.py:96
- **Description:** eval()
- **Evidence (Line):** `present_params = signature_no_eval(init).parameters.values()`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 141. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_typing_extra.py:458
- **Description:** eval()
- **Evidence (Line):** `def signature_no_eval(f: Callable[..., Any]) -> Signature:`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 142. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/_internal/_validate_call.py:107
- **Description:** eval()
- **Evidence (Line):** `signature = signature_no_eval(self.function)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 143. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/deprecated/parse.py:55
- **Description:** pickle load/dumps
- **Evidence (Line):** `return pickle.loads(bb)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 144. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/json_schema.py:1836
- **Description:** eval()
- **Evidence (Line):** `if len(_typing_extra.signature_no_eval(json_schema_extra).parameters) > 1:`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 145. [Critical] Hardcoded Secret
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/types.py:1835
- **Description:** Password Assignment detected
- **Evidence (Line):** `user = User(username='scolvin', password='password1')`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 146. [Critical] Hardcoded Secret
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/types.py:1862
- **Description:** Password Assignment detected
- **Evidence (Line):** `model = Model(password='IAmSensitive', password_bytes=b'IAmSensitiveBytes')`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 147. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/v1/parse.py:42
- **Description:** pickle load/dumps
- **Evidence (Line):** `return pickle.loads(bb)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 148. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/v1/utils.py:195
- **Description:** eval()
- **Evidence (Line):** `eval('__IPYTHON__')`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 149. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pydantic/validate_call_decorator.py:29
- **Description:** eval()
- **Evidence (Line):** `_typing_extra.signature_no_eval(cast(_generate_schema.ValidateCallSupportedTypes, function))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 150. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/formatters/__init__.py:91
- **Description:** eval()
- **Evidence (Line):** `this method is equivalent to running ``eval()`` on the input file. The formatter is`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 151. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/formatters/__init__.py:103
- **Description:** exec()
- **Evidence (Line):** `exec(f.read(), custom_namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 152. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/lexers/__init__.py:154
- **Description:** exec()
- **Evidence (Line):** `exec(f.read(), custom_namespace)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 153. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/lexers/_julia_builtins.py:150
- **Description:** eval()
- **Evidence (Line):** `v = eval(Symbol(compl.mod))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 154. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/lexers/_julia_builtins.py:361
- **Description:** eval()
- **Evidence (Line):** `v = eval(Symbol(compl.mod))`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 155. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/pygments/lexers/special.py:115
- **Description:** eval()
- **Evidence (Line):** `val = ast.literal_eval(val)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 156. [Critical] Insecure Deserialization
- **File:** .venv-test/lib/python3.12/site-packages/regex/tests/test_regex.py:3775
- **Description:** pickle load/dumps
- **Evidence (Line):** `r = pickle.loads(p)`
- **Exploit Scenario:** Attacker could achieve remote code execution
- **Fix Recommendation:** Use safe serialization formats (JSON), avoid pickle/yaml.load with untrusted data
- **Confidence:** High

### 157. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/rich/markup.py:190
- **Description:** eval()
- **Evidence (Line):** `meta_params = literal_eval(parameters)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 158. [Critical] Hardcoded Secret
- **File:** .venv-test/lib/python3.12/site-packages/starlette/datastructures.py:182
- **Description:** Password Assignment detected
- **Evidence (Line):** `url = str(self.replace(password="********"))`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 159. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:1591
- **Description:** eval()
- **Evidence (Line):** `(unless you are familiar with how eval() and exec() work).  The`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 160. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:4167
- **Description:** eval()
- **Evidence (Line):** `# as a way of emulating annotation scopes when calling `eval()``
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 161. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:4172
- **Description:** eval()
- **Evidence (Line):** `value if not isinstance(value, str) else eval(value, globals, locals)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 162. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:4219
- **Description:** eval()
- **Evidence (Line):** `# If we pass None to eval() below, the globals of this module are used.`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 163. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:4231
- **Description:** eval()
- **Evidence (Line):** `# as a way of emulating annotation scopes when calling `eval()``
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 164. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:4254
- **Description:** eval()
- **Evidence (Line):** `value = eval(code, globals, locals)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 165. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_extensions.py:1591
- **Description:** exec()
- **Evidence (Line):** `(unless you are familiar with how eval() and exec() work).  The`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 166. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_inspection/typing_objects.py:112
- **Description:** exec()
- **Evidence (Line):** `exec(func_code, globals_, locals_)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 167. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/typing_inspection/typing_objects.py:153
- **Description:** exec()
- **Evidence (Line):** `exec(func_code, globals_, locals_)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 168. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/websockets/cli.py:214
- **Description:** os.system()
- **Evidence (Line):** `os.system("")`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 169. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/werkzeug/debug/__init__.py:138
- **Description:** eval()
- **Evidence (Line):** `def eval(self, code: str) -> t.Any:`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 170. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/werkzeug/debug/__init__.py:139
- **Description:** eval()
- **Evidence (Line):** `return self.console.eval(code)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 171. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/werkzeug/debug/__init__.py:400
- **Description:** eval()
- **Evidence (Line):** `return Response(frame.eval(command), mimetype="text/html")`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 172. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/werkzeug/debug/console.py:213
- **Description:** eval()
- **Evidence (Line):** `def eval(self, code: str) -> str:`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 173. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/werkzeug/debug/console.py:177
- **Description:** exec()
- **Evidence (Line):** `exec(code, self.locals)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 174. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/werkzeug/debug/tbtools.py:391
- **Description:** eval()
- **Evidence (Line):** `def eval(self, code: str) -> t.Any:`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 175. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/werkzeug/debug/tbtools.py:392
- **Description:** eval()
- **Evidence (Line):** `return self.console.eval(code)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 176. [Critical] Command Injection
- **File:** .venv-test/lib/python3.12/site-packages/werkzeug/routing/rules.py:736
- **Description:** exec()
- **Evidence (Line):** `exec(code, globs, locs)`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 177. [Critical] Hardcoded Secret
- **File:** CUSTOM_PROVIDERS.md:67
- **Description:** API Key Assignment detected
- **Evidence (Line):** `api_key="your_runpod_api_key",`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 178. [Critical] Hardcoded Secret
- **File:** CUSTOM_PROVIDERS.md:92
- **Description:** API Key Assignment detected
- **Evidence (Line):** `api_key="your_llama_labs_key"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 179. [Critical] Hardcoded Secret
- **File:** CUSTOM_PROVIDERS.md:110
- **Description:** API Key Assignment detected
- **Evidence (Line):** `api_key="your_replicate_token"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 180. [Critical] Hardcoded Secret
- **File:** CUSTOM_PROVIDERS.md:129
- **Description:** API Key Assignment detected
- **Evidence (Line):** `api_key="your_together_api_key"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 181. [Critical] Hardcoded Secret
- **File:** CUSTOM_PROVIDERS.md:373
- **Description:** API Key Assignment detected
- **Evidence (Line):** `api_key="internal-auth-token",`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 182. [Critical] Hardcoded Secret
- **File:** tests/test_accuracy_verification.py:677
- **Description:** API Key Assignment detected
- **Evidence (Line):** `api_key="your-runpod-api-key",`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 183. [Critical] Hardcoded Secret
- **File:** tests/test_accuracy_verification.py:708
- **Description:** API Key Assignment detected
- **Evidence (Line):** `api_key="your-llama-labs-key",`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 184. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/authlib/oauth1/rfc5849/client_auth.py:148
- **Description:** SHA1 usage
- **Evidence (Line):** `oauth_body_hash = base64.b64encode(hashlib.sha1(body).digest())`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 185. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/authlib/oauth1/rfc5849/client_auth.py:148
- **Description:** Weak hash algorithm
- **Evidence (Line):** `oauth_body_hash = base64.b64encode(hashlib.sha1(body).digest())`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 186. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/authlib/oauth1/rfc5849/rsa.py:11
- **Description:** SHA1 usage
- **Evidence (Line):** `def sign_sha1(msg, rsa_private_key):`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 187. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/authlib/oauth1/rfc5849/rsa.py:18
- **Description:** SHA1 usage
- **Evidence (Line):** `def verify_sha1(sig, msg, rsa_public_key):`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 188. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/authlib/oauth1/rfc5849/signature.py:301
- **Description:** SHA1 usage
- **Evidence (Line):** `s = sign_sha1(to_bytes(base_string), rsa_private_key)`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 189. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/authlib/oauth1/rfc5849/signature.py:335
- **Description:** SHA1 usage
- **Evidence (Line):** `def sign_hmac_sha1(client, request):`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 190. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/authlib/oauth1/rfc5849/signature.py:341
- **Description:** SHA1 usage
- **Evidence (Line):** `def sign_rsa_sha1(client, request):`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 191. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/authlib/oauth1/rfc5849/signature.py:352
- **Description:** SHA1 usage
- **Evidence (Line):** `def verify_hmac_sha1(request):`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 192. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/authlib/oauth1/rfc5849/signature.py:359
- **Description:** SHA1 usage
- **Evidence (Line):** `def verify_rsa_sha1(request):`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 193. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/authlib/oauth1/rfc5849/signature.py:365
- **Description:** SHA1 usage
- **Evidence (Line):** `return verify_sha1(sig, to_bytes(base_string), request.rsa_public_key)`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 194. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/authlib/oauth1/rfc5849/signature.py:277
- **Description:** Weak hash algorithm
- **Evidence (Line):** `signature = hmac.new(to_bytes(key), to_bytes(text), hashlib.sha1)`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 195. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/hazmat/backends/openssl/backend.py:39
- **Description:** DES usage
- **Evidence (Line):** `# FIPS 140-3. To keep it simple we denylist any use of TripleDES (TDEA).`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 196. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/hazmat/decrepit/ciphers/algorithms.py:29
- **Description:** DES usage
- **Evidence (Line):** `class TripleDES(BlockCipherAlgorithm):`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 197. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/hazmat/decrepit/ciphers/algorithms.py:40
- **Description:** DES usage
- **Evidence (Line):** `"Single-key TripleDES (8-byte keys) is deprecated and "`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 198. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/hazmat/decrepit/ciphers/algorithms.py:49
- **Description:** DES usage
- **Evidence (Line):** `"Two-key TripleDES (16-byte keys) is deprecated and "`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 199. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/hazmat/decrepit/ciphers/algorithms.py:17
- **Description:** RC4 usage
- **Evidence (Line):** `class ARC4(CipherAlgorithm):`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 200. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/x509/extensions.py:72
- **Description:** SHA1 usage
- **Evidence (Line):** `return hashlib.sha1(data).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 201. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/cryptography/x509/extensions.py:72
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.sha1(data).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 202. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/dns/dnssec.py:224
- **Description:** SHA1 usage
- **Evidence (Line):** `dshash = hashlib.sha1()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 203. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/dns/dnssec.py:746
- **Description:** SHA1 usage
- **Evidence (Line):** `digest = hashlib.sha1(domain_encoded + salt_encoded).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 204. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/dns/dnssec.py:748
- **Description:** SHA1 usage
- **Evidence (Line):** `digest = hashlib.sha1(digest + salt_encoded).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 205. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/dns/dnssec.py:224
- **Description:** Weak hash algorithm
- **Evidence (Line):** `dshash = hashlib.sha1()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 206. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/dns/dnssec.py:746
- **Description:** Weak hash algorithm
- **Evidence (Line):** `digest = hashlib.sha1(domain_encoded + salt_encoded).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 207. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/dns/dnssec.py:748
- **Description:** Weak hash algorithm
- **Evidence (Line):** `digest = hashlib.sha1(digest + salt_encoded).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 208. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/dns/entropy.py:37
- **Description:** SHA1 usage
- **Evidence (Line):** `self.hash = hashlib.sha1()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 209. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/dns/entropy.py:37
- **Description:** Weak hash algorithm
- **Evidence (Line):** `self.hash = hashlib.sha1()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 210. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/dns/tsig.py:167
- **Description:** Weak hash algorithm
- **Evidence (Line):** `HMAC_SHA1: hashlib.sha1,`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 211. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/dns/tsig.py:175
- **Description:** Weak hash algorithm
- **Evidence (Line):** `HMAC_MD5: hashlib.md5,`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 212. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/fastmcp/server/providers/filesystem_discovery.py:136
- **Description:** SHA1 usage
- **Evidence (Line):** `digest = hashlib.sha1(`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 213. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/fastmcp/server/providers/filesystem_discovery.py:238
- **Description:** SHA1 usage
- **Evidence (Line):** `digest = hashlib.sha1(`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 214. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/fastmcp/server/providers/filesystem_discovery.py:136
- **Description:** Weak hash algorithm
- **Evidence (Line):** `digest = hashlib.sha1(`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 215. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/fastmcp/server/providers/filesystem_discovery.py:238
- **Description:** Weak hash algorithm
- **Evidence (Line):** `digest = hashlib.sha1(`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 216. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/flask/sessions.py:276
- **Description:** SHA1 usage
- **Evidence (Line):** `def _lazy_sha1(string: bytes = b"") -> t.Any:`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 217. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/flask/sessions.py:281
- **Description:** SHA1 usage
- **Evidence (Line):** `return hashlib.sha1(string)`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 218. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/flask/sessions.py:277
- **Description:** Weak hash algorithm
- **Evidence (Line):** `"""Don't access ``hashlib.sha1`` until runtime. FIPS builds may not include`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 219. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/flask/sessions.py:281
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.sha1(string)`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 220. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/httpx2/_auth.py:300
- **Description:** SHA1 usage
- **Evidence (Line):** `return hashlib.sha1(s).hexdigest()[:16].encode()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 221. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/httpx2/_auth.py:300
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.sha1(s).hexdigest()[:16].encode()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 222. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/hypothesis/extra/_patching.py:339
- **Description:** SHA1 usage
- **Evidence (Line):** `hash8 = hashlib.sha1(cleaned.encode()).hexdigest()[:8]`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 223. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/hypothesis/extra/_patching.py:339
- **Description:** Weak hash algorithm
- **Evidence (Line):** `hash8 = hashlib.sha1(cleaned.encode()).hexdigest()[:8]`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 224. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/hypothesis/internal/constants_ast.py:217
- **Description:** SHA1 usage
- **Evidence (Line):** `source_hash = hashlib.sha1(source_bytes).hexdigest()[:16]`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 225. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/hypothesis/internal/constants_ast.py:217
- **Description:** Weak hash algorithm
- **Evidence (Line):** `source_hash = hashlib.sha1(source_bytes).hexdigest()[:16]`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 226. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/itsdangerous/signer.py:40
- **Description:** SHA1 usage
- **Evidence (Line):** `def _lazy_sha1(string: bytes = b"") -> t.Any:`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 227. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/itsdangerous/signer.py:45
- **Description:** SHA1 usage
- **Evidence (Line):** `return hashlib.sha1(string)`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 228. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/itsdangerous/signer.py:41
- **Description:** Weak hash algorithm
- **Evidence (Line):** `"""Don't access ``hashlib.sha1`` until runtime. FIPS builds may not include`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 229. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/itsdangerous/signer.py:45
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.sha1(string)`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 230. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/itsdangerous/signer.py:96
- **Description:** Weak hash algorithm
- **Evidence (Line):** `defaults to :func:`hashlib.sha1`. Note that the security of the`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 231. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/itsdangerous/signer.py:115
- **Description:** Weak hash algorithm
- **Evidence (Line):** `#: :func:`hashlib.sha1`, but can be changed to any :mod:`hashlib` or`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 232. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/bccache.py:156
- **Description:** SHA1 usage
- **Evidence (Line):** `hash = sha1(name.encode("utf-8"))`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 233. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/bccache.py:165
- **Description:** SHA1 usage
- **Evidence (Line):** `return sha1(source.encode("utf-8")).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 234. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/jinja2/loaders.py:661
- **Description:** SHA1 usage
- **Evidence (Line):** `return "tmpl_" + sha1(name.encode("utf-8")).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 235. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/requests/auth.py:179
- **Description:** MD5 usage
- **Evidence (Line):** `return hashlib.md5(x, usedforsecurity=False).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 236. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/requests/auth.py:187
- **Description:** SHA1 usage
- **Evidence (Line):** `return hashlib.sha1(x, usedforsecurity=False).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 237. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/requests/auth.py:237
- **Description:** SHA1 usage
- **Evidence (Line):** `cnonce = hashlib.sha1(s, usedforsecurity=False).hexdigest()[:16]`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 238. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/requests/auth.py:179
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.md5(x, usedforsecurity=False).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 239. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/requests/auth.py:187
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.sha1(x, usedforsecurity=False).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 240. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/requests/auth.py:237
- **Description:** Weak hash algorithm
- **Evidence (Line):** `cnonce = hashlib.sha1(s, usedforsecurity=False).hexdigest()[:16]`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 241. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/rich/tree.py:18
- **Description:** DES usage
- **Evidence (Line):** `ASCII_GUIDES (GuideType): Guide lines used when Console.ascii_only is True.`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 242. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/rich/tree.py:19
- **Description:** DES usage
- **Evidence (Line):** `TREE_GUIDES (List[GuideType, GuideType, GuideType]): Default guide lines.`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 243. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/starlette/responses.py:340
- **Description:** MD5 usage
- **Evidence (Line):** `etag = f'"{hashlib.md5(etag_base.encode(), usedforsecurity=False).hexdigest()}"'`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 244. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/starlette/responses.py:340
- **Description:** Weak hash algorithm
- **Evidence (Line):** `etag = f'"{hashlib.md5(etag_base.encode(), usedforsecurity=False).hexdigest()}"'`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 245. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/tiktoken/load.py:51
- **Description:** SHA1 usage
- **Evidence (Line):** `cache_key = hashlib.sha1(blobpath.encode()).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 246. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/tiktoken/load.py:51
- **Description:** Weak hash algorithm
- **Evidence (Line):** `cache_key = hashlib.sha1(blobpath.encode()).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 247. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/websockets/utils.py:35
- **Description:** SHA1 usage
- **Evidence (Line):** `sha1 = hashlib.sha1((key + GUID).encode()).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 248. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/websockets/utils.py:35
- **Description:** Weak hash algorithm
- **Evidence (Line):** `sha1 = hashlib.sha1((key + GUID).encode()).digest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 249. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/werkzeug/debug/__init__.py:45
- **Description:** SHA1 usage
- **Evidence (Line):** `return hashlib.sha1(f"{pin} added salt".encode("utf-8", "replace")).hexdigest()[:12]`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 250. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/werkzeug/debug/__init__.py:196
- **Description:** SHA1 usage
- **Evidence (Line):** `h = hashlib.sha1()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 251. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/werkzeug/debug/__init__.py:45
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.sha1(f"{pin} added salt".encode("utf-8", "replace")).hexdigest()[:12]`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 252. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/werkzeug/debug/__init__.py:196
- **Description:** Weak hash algorithm
- **Evidence (Line):** `h = hashlib.sha1()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 253. [Medium] Weak Cryptography
- **File:** .venv-test/lib/python3.12/site-packages/werkzeug/http.py:1077
- **Description:** SHA1 usage
- **Evidence (Line):** `return sha1(data).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High
