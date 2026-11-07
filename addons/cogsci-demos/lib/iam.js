// The interactive activation model of letter perception (McClelland &
// Rumelhart, 1981), small enough to run live on a slide. Used by
// <InteractiveActivation>; kept framework-free so it can be tested in node.
//
// Three levels: feature detectors (14 line segments, each "present" or
// "absent", in each of four letter positions), letter units (26 per
// position), and word units (one per four-letter word). Units update with
// the equations on the lecture slides:
//
//   n_i(t)   = Σ excitation − Σ inhibition (from units with a_j > 0)
//   e_i(t)   = n_i (max − a_i)   if n_i > 0
//            = n_i (a_i − min)   if n_i < 0
//   a_i(t+1) = a_i − decay (a_i − rest_i) + e_i
//
// Parameter values follow the 1981 paper. Simplifications: a 14-segment font
// stands in for the Rumelhart–Siple font, word resting levels span a small
// range set by modern word frequencies, and features are clamped on rather
// than fading under a mask.
import { LEXICON } from './iam-lexicon.js'

export const PARAMS = {
  featureLetterExc: 0.005,
  featureLetterInh: 0.15,
  letterWordExc: 0.07,
  letterWordInh: 0.04,
  wordWordInh: 0.21,
  wordLetterExc: 0.3,
  decay: 0.07,
  max: 1,
  min: -0.2,
  letterRest: 0,
  wordRestRange: 0.05, // most frequent word rests at 0, least at −0.05
}

// ---- 14-segment font --------------------------------------------------
// Segment endpoints in a 10 × 14 box (x right, y down).
export const SEGMENTS = [
  [1, 1, 9, 1], // 0 top
  [9, 1, 9, 7], // 1 upper right
  [9, 7, 9, 13], // 2 lower right
  [1, 13, 9, 13], // 3 bottom
  [1, 7, 1, 13], // 4 lower left
  [1, 1, 1, 7], // 5 upper left
  [1, 7, 5, 7], // 6 middle left
  [5, 7, 9, 7], // 7 middle right
  [1, 1, 5, 7], // 8 upper-left diagonal
  [5, 1, 5, 7], // 9 upper centre
  [9, 1, 5, 7], // 10 upper-right diagonal
  [5, 7, 1, 13], // 11 lower-left diagonal
  [5, 7, 5, 13], // 12 lower centre
  [5, 7, 9, 13], // 13 lower-right diagonal
]
export const FONT = {
  A: [0, 1, 2, 4, 5, 6, 7],
  B: [0, 1, 2, 3, 7, 9, 12],
  C: [0, 3, 4, 5],
  D: [0, 1, 2, 3, 9, 12],
  E: [0, 3, 4, 5, 6],
  F: [0, 4, 5, 6],
  G: [0, 2, 3, 4, 5, 7],
  H: [1, 2, 4, 5, 6, 7],
  I: [0, 3, 9, 12],
  J: [1, 2, 3, 4],
  K: [4, 5, 6, 10, 13],
  L: [3, 4, 5],
  M: [1, 2, 4, 5, 8, 10],
  N: [1, 2, 4, 5, 8, 13],
  O: [0, 1, 2, 3, 4, 5],
  P: [0, 1, 4, 5, 6, 7],
  Q: [0, 1, 2, 3, 4, 5, 13],
  R: [0, 1, 4, 5, 6, 7, 13],
  S: [0, 2, 3, 7, 8],
  T: [0, 9, 12],
  U: [1, 2, 3, 4, 5],
  V: [4, 5, 10, 11],
  W: [1, 2, 4, 5, 11, 13],
  X: [8, 10, 11, 13],
  Y: [8, 10, 12],
  Z: [0, 3, 10, 11],
}
export const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')
const NF = SEGMENTS.length
const NL = LETTERS.length
const hasSeg = LETTERS.map(l => {
  const v = new Array(NF).fill(false)
  for (const s of FONT[l]) v[s] = true
  return v
})

// ---- lexicon -----------------------------------------------------------
export const WORDS = []
export const ZIPF = []
for (const tok of LEXICON.split(' ')) {
  const [w, z] = tok.split(':')
  WORDS.push(w.toUpperCase())
  ZIPF.push(+z)
}
const NW = WORDS.length
const wordLetters = WORDS.map(w => [...w].map(c => c.charCodeAt(0) - 65))
const zmax = Math.max(...ZIPF), zmin = Math.min(...ZIPF)
const wordRest = ZIPF.map(z => -PARAMS.wordRestRange * (zmax - z) / (zmax - zmin))
// words with letter l in position p, for word → letter feedback
const wordsWith = Array.from({ length: 4 }, (_, p) => Array.from({ length: NL }, (_, l) =>
  wordLetters.map((ls, w) => (ls[p] === l ? w : -1)).filter(w => w >= 0)))

// ---- display → feature input ----------------------------------------------
// display: array of 4 entries; each is null (nothing shown in that position)
// or { letter, hidden: [segment indices covered up] }. The letter '#' is a
// mask: every segment present. Returns, per position,
// an array of 14 values: 1 present, 0 absent, null unknown.
export function featuresOf(display) {
  return display.map(d => {
    if (!d || !(FONT[d.letter] || d.letter === '#')) return new Array(NF).fill(null)
    const on = new Set(d.letter === '#' ? SEGMENTS.map((_, s) => s) : FONT[d.letter])
    const hid = new Set(d.hidden || [])
    return SEGMENTS.map((_, s) => (hid.has(s) ? null : on.has(s) ? 1 : 0))
  })
}

export function createModel(params = {}) {
  const P = { ...PARAMS, ...params }
  const letters = Array.from({ length: 4 }, () => new Float64Array(NL).fill(P.letterRest))
  const words = Float64Array.from(wordRest)
  let features = featuresOf([null, null, null, null])
  let cycle = 0

  function update(a, n, rest) {
    const e = n > 0 ? n * (P.max - a) : n * (a - P.min)
    let v = a - P.decay * (a - rest) + e
    return v > P.max ? P.max : v < P.min ? P.min : v
  }

  function step() {
    // net input to letters: features (bottom-up) + words (top-down)
    const lNet = letters.map(() => new Float64Array(NL))
    for (let p = 0; p < 4; p++) {
      const f = features[p]
      for (let l = 0; l < NL; l++) {
        let n = 0
        for (let s = 0; s < NF; s++) {
          if (f[s] === null) continue
          const consistent = (f[s] === 1) === hasSeg[l][s]
          n += consistent ? P.featureLetterExc : -P.featureLetterInh
        }
        let top = 0
        for (const w of wordsWith[p][l]) if (words[w] > 0) top += words[w]
        lNet[p][l] = n + P.wordLetterExc * top
      }
    }
    // net input to words: letters (bottom-up) + competition among words
    let wordSum = 0
    for (let w = 0; w < NW; w++) if (words[w] > 0) wordSum += words[w]
    const wNet = new Float64Array(NW)
    for (let w = 0; w < NW; w++) {
      let n = 0
      for (let p = 0; p < 4; p++) {
        const mine = wordLetters[w][p]
        const L = letters[p]
        for (let l = 0; l < NL; l++) {
          if (L[l] <= 0) continue
          n += l === mine ? P.letterWordExc * L[l] : -P.letterWordInh * L[l]
        }
      }
      n -= P.wordWordInh * (wordSum - Math.max(words[w], 0))
      wNet[w] = n
    }
    for (let p = 0; p < 4; p++) for (let l = 0; l < NL; l++) letters[p][l] = update(letters[p][l], lNet[p][l], P.letterRest)
    for (let w = 0; w < NW; w++) words[w] = update(words[w], wNet[w], wordRest[w])
    cycle++
  }

  function reset() {
    for (const L of letters) L.fill(P.letterRest)
    words.set(wordRest)
    cycle = 0
  }

  return {
    get cycle() { return cycle },
    setDisplay(display) { features = featuresOf(display) },
    step,
    reset,
    letter: (p, l) => letters[p][typeof l === 'string' ? l.charCodeAt(0) - 65 : l],
    word: w => words[typeof w === 'string' ? WORDS.indexOf(w) : w],
    topLetters(p, k = 5) {
      return LETTERS.map((l, i) => ({ name: l, a: letters[p][i] })).sort((x, y) => y.a - x.a).slice(0, k)
    },
    topWords(k = 6) {
      const idx = Array.from(words.keys()).sort((x, y) => words[y] - words[x]).slice(0, k)
      return idx.map(i => ({ name: WORDS[i], a: words[i] }))
    },
  }
}

export const isWord = s => WORDS.includes(s.toUpperCase())
