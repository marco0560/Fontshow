#!/usr/bin/env bash
#
# Purpose
# -------
# Execute the guarded release push workflow.
#
# Responsibilities
# ----------------
# - Configure the environment required for the release push path.
# - Invoke the release audit script in the expected release mode.
# - Push the repository only after the guarded release path is established.
#
# Design principles
# -----------------
# This wrapper must remain minimal and explicit. It centralizes the release
# invocation sequence so the push path is reproducible and easy to inspect.
#
set -euo pipefail

bash scripts/release_audit.sh

SKIP_RELEASE_AUDIT=1 ALLOW_MAIN_PUSH=1 git push
