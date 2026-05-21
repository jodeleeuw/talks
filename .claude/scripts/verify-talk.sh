#!/usr/bin/env bash
# verify-talk.sh — build and visually verify a Slidev talk in one shot.
#
# Usage:
#   .claude/scripts/verify-talk.sh <talk-dir> [--port N] [--shots N|all] [--out DIR]
#
#   <talk-dir>   path to the talk directory (must contain slides.md + package.json)
#   --port N     dev server port (default: 3030). If taken, falls back to next free port.
#   --shots S    which slides to screenshot. "all" (default), "none", or "1,3,5-7".
#   --out DIR    where to write PNGs (default: <talk-dir>/_shots/)
#
# Does, in order:
#   1. npm install (if node_modules missing or package.json newer)
#   2. npx slidev build → check exit code, then rm -rf dist
#   3. start `npm run dev`, wait until HTTP 200 on / (timeout 30s)
#   4. headless-chrome screenshot each requested slide to <out>/slide-N.png
#   5. stop dev server
#   6. print one line per shot (path + http status)
#
# On any failure: print error context, stop dev server, exit non-zero.

set -uo pipefail

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

die() { echo "verify-talk: $*" >&2; cleanup; exit 1; }

# ---- arg parsing ------------------------------------------------------------

TALK_DIR=""
PORT=3030
SHOTS="all"
OUT_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)  PORT="$2"; shift 2 ;;
    --shots) SHOTS="$2"; shift 2 ;;
    --out)   OUT_DIR="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    -*) die "unknown flag: $1" ;;
    *)
      [[ -z "$TALK_DIR" ]] && TALK_DIR="$1" || die "unexpected arg: $1"
      shift ;;
  esac
done

[[ -z "$TALK_DIR" ]] && die "missing <talk-dir>"
[[ -d "$TALK_DIR" ]] || die "no such dir: $TALK_DIR"
[[ -f "$TALK_DIR/slides.md" ]] || die "$TALK_DIR has no slides.md"
[[ -f "$TALK_DIR/package.json" ]] || die "$TALK_DIR has no package.json"

TALK_DIR="$(cd "$TALK_DIR" && pwd)"
[[ -z "$OUT_DIR" ]] && OUT_DIR="$TALK_DIR/_shots"
mkdir -p "$OUT_DIR"

DEV_PID=""
DEV_LOG=""

cleanup() {
  [[ -n "$DEV_PID" ]] && kill "$DEV_PID" 2>/dev/null
  DEV_PID=""
}
trap cleanup EXIT INT TERM

# ---- 1. npm install ---------------------------------------------------------

cd "$TALK_DIR"

if [[ ! -d node_modules ]] || [[ package.json -nt node_modules ]]; then
  echo "verify-talk: npm install"
  npm install --no-audit --no-fund --silent 2>&1 | tail -5 || die "npm install failed"
fi

# ---- 2. build --------------------------------------------------------------

echo "verify-talk: npx slidev build"
BUILD_LOG="$(mktemp -t verify-talk-build.XXXXXX)"
if ! npx slidev build > "$BUILD_LOG" 2>&1; then
  echo "verify-talk: BUILD FAILED:" >&2
  tail -40 "$BUILD_LOG" >&2
  rm -f "$BUILD_LOG"
  exit 1
fi
SLIDE_COUNT="$(grep -oE 'dist/[0-9]+\.html' "$BUILD_LOG" | sort -u | wc -l | tr -d ' ')"
[[ "$SLIDE_COUNT" -eq 0 ]] && SLIDE_COUNT="$(grep -cE '^# ' "$TALK_DIR/slides.md" || echo 0)"
rm -f "$BUILD_LOG"
rm -rf "$TALK_DIR/dist"
echo "verify-talk: build OK"

# ---- skip screenshots? -----------------------------------------------------

if [[ "$SHOTS" == "none" ]]; then
  echo "verify-talk: shots=none — skipping dev/screenshots"
  exit 0
fi

# ---- 3. start dev ----------------------------------------------------------

# find a free port if PORT is taken
START_PORT="$PORT"
while lsof -ti:"$PORT" >/dev/null 2>&1; do
  PORT=$((PORT + 1))
  [[ "$PORT" -gt $((START_PORT + 20)) ]] && die "no free port in $START_PORT..$PORT"
done

DEV_LOG="$(mktemp -t verify-talk-dev.XXXXXX)"
echo "verify-talk: starting dev on :$PORT"
(npx slidev --port "$PORT" > "$DEV_LOG" 2>&1) &
DEV_PID=$!

# wait for HTTP 200
DEV_URL="http://localhost:$PORT"
for _ in {1..60}; do
  curl -sf "$DEV_URL/" -o /dev/null && break
  sleep 0.5
done
curl -sf "$DEV_URL/" -o /dev/null || {
  echo "verify-talk: dev server didn't start in 30s:" >&2
  tail -20 "$DEV_LOG" >&2
  rm -f "$DEV_LOG"
  exit 1
}
echo "verify-talk: dev ready at $DEV_URL"

# ---- expand SHOTS spec into a list of ints ---------------------------------

if [[ "$SHOTS" == "all" ]]; then
  # count slides by parsing entries from the dev server's overview index
  TOTAL="$(curl -sf "$DEV_URL/overview" -o /dev/null && \
           curl -sf "$DEV_URL/1" -o /dev/null && echo "$SLIDE_COUNT")"
  TOTAL="${TOTAL:-$SLIDE_COUNT}"
  [[ "$TOTAL" -eq 0 ]] && TOTAL=99
  # probe forward until 404 / non-200
  SHOT_LIST=()
  for n in $(seq 1 "$TOTAL"); do
    code="$(curl -s -o /dev/null -w '%{http_code}' "$DEV_URL/$n")"
    [[ "$code" == "200" ]] || break
    SHOT_LIST+=("$n")
  done
else
  SHOT_LIST=()
  IFS=',' read -ra parts <<< "$SHOTS"
  for p in "${parts[@]}"; do
    if [[ "$p" =~ ^([0-9]+)-([0-9]+)$ ]]; then
      for n in $(seq "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"); do
        SHOT_LIST+=("$n")
      done
    else
      SHOT_LIST+=("$p")
    fi
  done
fi

# ---- 4. screenshot --------------------------------------------------------

echo "verify-talk: shooting ${#SHOT_LIST[@]} slides → $OUT_DIR"
FAILS=0
for n in "${SHOT_LIST[@]}"; do
  out="$OUT_DIR/slide-$n.png"
  code="$(curl -s -o /dev/null -w '%{http_code}' "$DEV_URL/$n")"
  if [[ "$code" != "200" ]]; then
    echo "  slide $n: HTTP $code (skipped)"
    FAILS=$((FAILS + 1))
    continue
  fi
  "$CHROME" --headless --disable-gpu --window-size=1600,900 \
    --hide-scrollbars --virtual-time-budget=4500 \
    --screenshot="$out" "$DEV_URL/$n" >/dev/null 2>&1
  if [[ -s "$out" ]]; then
    echo "  slide $n: $out"
  else
    echo "  slide $n: screenshot empty"
    FAILS=$((FAILS + 1))
  fi
done

rm -f "$DEV_LOG"

if [[ "$FAILS" -gt 0 ]]; then
  echo "verify-talk: $FAILS slide(s) failed to screenshot" >&2
  exit 1
fi
echo "verify-talk: done"
