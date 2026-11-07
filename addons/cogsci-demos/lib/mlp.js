// A tiny two-input, one-hidden-layer network (tanh hidden units, sigmoid
// output, cross-entropy loss, optional L2 weight decay) trained with Adam on
// the full batch. Used by <OverfitPlayground>; framework-free.
import { gauss, rng } from './plot.js'

export function createNet(hidden, seed = 1) {
  const H = hidden
  const r = rng(seed)
  const P = {
    W1: Array.from({ length: H }, () => [gauss(r), gauss(r)]),
    b1: Array.from({ length: H }, () => gauss(r) * 0.5),
    W2: Array.from({ length: H }, () => gauss(r) / Math.sqrt(H)),
    b2: [0],
  }
  const zeros = o => (Array.isArray(o) ? o.map(zeros) : 0)
  const M = zeros(Object.values(P)), V = zeros(Object.values(P))
  let t = 0

  function forward(x, y) {
    const h = new Array(H)
    let z = P.b2[0]
    for (let j = 0; j < H; j++) {
      h[j] = Math.tanh(P.W1[j][0] * x + P.W1[j][1] * y + P.b1[j])
      z += h[j] * P.W2[j]
    }
    return { h, p: 1 / (1 + Math.exp(-z)) }
  }
  const predict = (x, y) => forward(x, y).p

  // mean cross-entropy on [[x, y, label], …]
  function loss(data) {
    let L = 0
    for (const [x, y, c] of data) {
      const p = Math.min(1 - 1e-7, Math.max(1e-7, predict(x, y)))
      L -= c ? Math.log(p) : Math.log(1 - p)
    }
    return L / data.length
  }
  const errorRate = data => data.filter(([x, y, c]) => (predict(x, y) >= 0.5 ? 1 : 0) !== c).length / data.length

  function train(data, lr = 0.005, decay = 0) {
    const G = { W1: P.W1.map(() => [0, 0]), b1: new Array(H).fill(0), W2: new Array(H).fill(0), b2: [0] }
    for (const [x, y, c] of data) {
      const { h, p } = forward(x, y)
      const dz = (p - c) / data.length
      G.b2[0] += dz
      for (let j = 0; j < H; j++) {
        G.W2[j] += dz * h[j]
        const dh = dz * P.W2[j] * (1 - h[j] * h[j])
        G.W1[j][0] += dh * x; G.W1[j][1] += dh * y; G.b1[j] += dh
      }
    }
    for (let j = 0; j < H; j++) { G.W2[j] += decay * P.W2[j]; G.W1[j][0] += decay * P.W1[j][0]; G.W1[j][1] += decay * P.W1[j][1] }
    t++
    const c1 = 1 - 0.9 ** t, c2 = 1 - 0.999 ** t
    const step = (p, g, m, v) => {
      for (let i = 0; i < p.length; i++) {
        if (Array.isArray(p[i])) { step(p[i], g[i], m[i], v[i]); continue }
        m[i] = 0.9 * m[i] + 0.1 * g[i]
        v[i] = 0.999 * v[i] + 0.001 * g[i] * g[i]
        p[i] -= (lr * (m[i] / c1)) / (Math.sqrt(v[i] / c2) + 1e-8)
      }
    }
    step(Object.values(P), Object.values(G), M, V)
  }

  return { predict, loss, errorRate, train, get epoch() { return t } }
}

// Points in [-1, 1]² labelled by a gently curving boundary, with a fraction
// of labels flipped (noise the network can memorise but shouldn't).
export function makeData(seed, n, flip = 0.15) {
  const r = rng(seed)
  const out = []
  for (let k = 0; k < n; k++) {
    const x = r(), y = r()
    let c = x < 0.5 + 0.1 * Math.sin(3 * y) ? 0 : 1
    if (r() < flip) c = 1 - c
    out.push([x * 2 - 1, y * 2 - 1, c])
  }
  return out
}
