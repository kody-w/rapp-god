const BLOCKS_M = {
  1: [{ count: 1, total: 26, data: 16 }],
  2: [{ count: 1, total: 44, data: 28 }],
  3: [{ count: 1, total: 70, data: 44 }],
  4: [{ count: 2, total: 50, data: 32 }],
  5: [{ count: 2, total: 67, data: 43 }],
  6: [{ count: 4, total: 43, data: 27 }],
  7: [{ count: 4, total: 49, data: 31 }],
  8: [{ count: 2, total: 60, data: 38 }, { count: 2, total: 61, data: 39 }],
  9: [{ count: 3, total: 58, data: 36 }, { count: 2, total: 59, data: 37 }],
  10: [{ count: 4, total: 69, data: 43 }, { count: 1, total: 70, data: 44 }],
  11: [{ count: 1, total: 80, data: 50 }, { count: 4, total: 81, data: 51 }],
  12: [{ count: 6, total: 58, data: 36 }, { count: 2, total: 59, data: 37 }],
  13: [{ count: 8, total: 59, data: 37 }, { count: 1, total: 60, data: 38 }],
  14: [{ count: 4, total: 64, data: 40 }, { count: 5, total: 65, data: 41 }],
  15: [{ count: 5, total: 65, data: 41 }, { count: 5, total: 66, data: 42 }],
  16: [{ count: 7, total: 73, data: 45 }, { count: 3, total: 74, data: 46 }],
  17: [{ count: 10, total: 74, data: 46 }, { count: 1, total: 75, data: 47 }],
  18: [{ count: 9, total: 69, data: 43 }, { count: 4, total: 70, data: 44 }],
  19: [{ count: 3, total: 70, data: 44 }, { count: 11, total: 71, data: 45 }],
  20: [{ count: 3, total: 67, data: 41 }, { count: 13, total: 68, data: 42 }],
  21: [{ count: 17, total: 68, data: 42 }],
  22: [{ count: 17, total: 74, data: 46 }],
  23: [{ count: 4, total: 75, data: 47 }, { count: 14, total: 76, data: 48 }],
  24: [{ count: 6, total: 73, data: 45 }, { count: 14, total: 74, data: 46 }],
  25: [{ count: 8, total: 75, data: 47 }, { count: 13, total: 76, data: 48 }]
};

const ALIGNMENT_CENTERS = {
  1: [],
  2: [6, 18],
  3: [6, 22],
  4: [6, 26],
  5: [6, 30],
  6: [6, 34],
  7: [6, 22, 38],
  8: [6, 24, 42],
  9: [6, 26, 46],
  10: [6, 28, 50],
  11: [6, 30, 54],
  12: [6, 32, 58],
  13: [6, 34, 62],
  14: [6, 26, 46, 66],
  15: [6, 26, 48, 70],
  16: [6, 26, 50, 74],
  17: [6, 30, 54, 78],
  18: [6, 30, 56, 82],
  19: [6, 30, 58, 86],
  20: [6, 34, 62, 90],
  21: [6, 28, 50, 72, 94],
  22: [6, 26, 50, 74, 98],
  23: [6, 30, 54, 78, 102],
  24: [6, 28, 54, 80, 106],
  25: [6, 32, 58, 84, 110]
};

const GF_EXP = new Uint8Array(512);
const GF_LOG = new Uint8Array(256);
let gfValue = 1;
for (let i = 0; i < 255; i++) {
  GF_EXP[i] = gfValue;
  GF_LOG[gfValue] = i;
  gfValue <<= 1;
  if (gfValue & 0x100) gfValue ^= 0x11d;
}
for (let i = 255; i < GF_EXP.length; i++) GF_EXP[i] = GF_EXP[i - 255];

function gfMultiply(a, b) {
  return a && b ? GF_EXP[GF_LOG[a] + GF_LOG[b]] : 0;
}

function multiplyPolynomials(a, b) {
  const result = new Uint8Array(a.length + b.length - 1);
  for (let i = 0; i < a.length; i++)
    for (let j = 0; j < b.length; j++)
      result[i + j] ^= gfMultiply(a[i], b[j]);
  return [...result];
}

function errorCorrection(data, count) {
  let generator = [1];
  for (let i = 0; i < count; i++) generator = multiplyPolynomials(generator, [1, GF_EXP[i]]);
  const remainder = [...data, ...new Array(count).fill(0)];
  for (let i = 0; i < data.length; i++) {
    const factor = remainder[i];
    if (!factor) continue;
    for (let j = 0; j < generator.length; j++)
      remainder[i + j] ^= gfMultiply(generator[j], factor);
  }
  return remainder.slice(data.length);
}

function appendBits(bits, value, length) {
  for (let i = length - 1; i >= 0; i--) bits.push((value >>> i) & 1);
}

function makeCodewords(bytes, version) {
  const definitions = BLOCKS_M[version];
  const dataCapacity = definitions.reduce((total, block) => total + block.count * block.data, 0);
  const countBits = version < 10 ? 8 : 16;
  const bits = [];
  appendBits(bits, 0b0100, 4);
  appendBits(bits, bytes.length, countBits);
  for (const byte of bytes) appendBits(bits, byte, 8);
  const capacityBits = dataCapacity * 8;
  for (let i = 0; i < Math.min(4, capacityBits - bits.length); i++) bits.push(0);
  while (bits.length % 8) bits.push(0);
  const data = [];
  for (let i = 0; i < bits.length; i += 8) {
    let byte = 0;
    for (let j = 0; j < 8; j++) byte = (byte << 1) | bits[i + j];
    data.push(byte);
  }
  for (let pad = 0; data.length < dataCapacity; pad++)
    data.push(pad % 2 ? 0x11 : 0xec);

  const blocks = [];
  let offset = 0;
  for (const definition of definitions) {
    for (let i = 0; i < definition.count; i++) {
      const chunk = data.slice(offset, offset + definition.data);
      offset += definition.data;
      blocks.push({ data: chunk, ec: errorCorrection(chunk, definition.total - definition.data) });
    }
  }
  const result = [];
  const maxData = Math.max(...blocks.map(block => block.data.length));
  const maxEc = Math.max(...blocks.map(block => block.ec.length));
  for (let i = 0; i < maxData; i++)
    for (const block of blocks) if (i < block.data.length) result.push(block.data[i]);
  for (let i = 0; i < maxEc; i++)
    for (const block of blocks) if (i < block.ec.length) result.push(block.ec[i]);
  return result;
}

function emptyMatrix(version) {
  const size = version * 4 + 17;
  return Array.from({ length: size }, () => new Array(size).fill(null));
}

function placeFinder(matrix, x, y) {
  const size = matrix.length;
  for (let dy = -1; dy <= 7; dy++) {
    for (let dx = -1; dx <= 7; dx++) {
      const row = y + dy, col = x + dx;
      if (row < 0 || col < 0 || row >= size || col >= size) continue;
      matrix[row][col] = dx >= 0 && dx <= 6 && dy >= 0 && dy <= 6 &&
        (dx === 0 || dx === 6 || dy === 0 || dy === 6 ||
         (dx >= 2 && dx <= 4 && dy >= 2 && dy <= 4));
    }
  }
}

function placeAlignment(matrix, x, y) {
  for (let dy = -2; dy <= 2; dy++)
    for (let dx = -2; dx <= 2; dx++) {
      const distance = Math.max(Math.abs(dx), Math.abs(dy));
      matrix[y + dy][x + dx] = distance === 2 || distance === 0;
    }
}

function bchFormat(value) {
  let remainder = value << 10;
  const generator = 0x537;
  const degree = number => 31 - Math.clz32(number);
  while (degree(remainder) >= degree(generator))
    remainder ^= generator << (degree(remainder) - degree(generator));
  return ((value << 10) | remainder) ^ 0x5412;
}

function placeFormat(matrix, mask) {
  const size = matrix.length;
  const bits = bchFormat(mask);
  for (let i = 0; i < 15; i++) {
    const dark = ((bits >>> i) & 1) === 1;
    if (i < 6) matrix[i][8] = dark;
    else if (i < 8) matrix[i + 1][8] = dark;
    else matrix[size - 15 + i][8] = dark;

    if (i < 8) matrix[8][size - i - 1] = dark;
    else if (i < 9) matrix[8][15 - i] = dark;
    else matrix[8][15 - i - 1] = dark;
  }
  matrix[size - 8][8] = true;
}

function placeVersion(matrix, version) {
  if (version < 7) return;
  let remainder = version << 12;
  const generator = 0x1f25;
  const degree = number => 31 - Math.clz32(number);
  while (degree(remainder) >= degree(generator))
    remainder ^= generator << (degree(remainder) - degree(generator));
  const bits = (version << 12) | remainder;
  const offset = matrix.length - 11;
  for (let i = 0; i < 18; i++) {
    const dark = ((bits >>> i) & 1) === 1;
    matrix[Math.floor(i / 3)][offset + i % 3] = dark;
    matrix[offset + i % 3][Math.floor(i / 3)] = dark;
  }
}

function buildBase(version) {
  const matrix = emptyMatrix(version);
  const size = matrix.length;
  placeFinder(matrix, 0, 0);
  placeFinder(matrix, size - 7, 0);
  placeFinder(matrix, 0, size - 7);
  for (const y of ALIGNMENT_CENTERS[version])
    for (const x of ALIGNMENT_CENTERS[version])
      if (matrix[y][x] == null) placeAlignment(matrix, x, y);
  for (let i = 8; i < size - 8; i++) {
    if (matrix[6][i] == null) matrix[6][i] = i % 2 === 0;
    if (matrix[i][6] == null) matrix[i][6] = i % 2 === 0;
  }
  placeFormat(matrix, 0);
  placeVersion(matrix, version);
  return matrix;
}

const MASKS = [
  (row, col) => (row + col) % 2 === 0,
  row => row % 2 === 0,
  (_, col) => col % 3 === 0,
  (row, col) => (row + col) % 3 === 0,
  (row, col) => (Math.floor(row / 2) + Math.floor(col / 3)) % 2 === 0,
  (row, col) => (row * col) % 2 + (row * col) % 3 === 0,
  (row, col) => ((row * col) % 2 + (row * col) % 3) % 2 === 0,
  (row, col) => ((row + col) % 2 + (row * col) % 3) % 2 === 0
];

function placeData(matrix, codewords, mask) {
  const size = matrix.length;
  let row = size - 1, direction = -1, bitIndex = 0;
  for (let right = size - 1; right > 0; right -= 2) {
    if (right === 6) right--;
    while (true) {
      for (let offset = 0; offset < 2; offset++) {
        const col = right - offset;
        if (matrix[row][col] != null) continue;
        const byte = codewords[Math.floor(bitIndex / 8)] || 0;
        let dark = ((byte >>> (7 - bitIndex % 8)) & 1) === 1;
        if (MASKS[mask](row, col)) dark = !dark;
        matrix[row][col] = dark;
        bitIndex++;
      }
      row += direction;
      if (row < 0 || row >= size) {
        row -= direction;
        direction = -direction;
        break;
      }
    }
  }
}

function penalty(matrix) {
  const size = matrix.length;
  let score = 0, darkCount = 0;
  const scoreRuns = line => {
    let value = line[0], length = 1, total = 0;
    for (let i = 1; i <= line.length; i++) {
      if (i < line.length && line[i] === value) length++;
      else {
        if (length >= 5) total += 3 + length - 5;
        value = line[i];
        length = 1;
      }
    }
    return total;
  };
  for (let row = 0; row < size; row++) {
    score += scoreRuns(matrix[row]);
    score += scoreRuns(matrix.map(line => line[row]));
    darkCount += matrix[row].filter(Boolean).length;
  }
  for (let row = 0; row < size - 1; row++)
    for (let col = 0; col < size - 1; col++) {
      const value = matrix[row][col];
      if (matrix[row + 1][col] === value && matrix[row][col + 1] === value && matrix[row + 1][col + 1] === value)
        score += 3;
    }
  const patterns = ['10111010000', '00001011101'];
  for (let row = 0; row < size; row++) {
    const horizontal = matrix[row].map(Number).join('');
    const vertical = matrix.map(line => Number(line[row])).join('');
    for (const pattern of patterns) {
      for (let index = horizontal.indexOf(pattern); index >= 0; index = horizontal.indexOf(pattern, index + 1)) score += 40;
      for (let index = vertical.indexOf(pattern); index >= 0; index = vertical.indexOf(pattern, index + 1)) score += 40;
    }
  }
  score += Math.floor(Math.abs(darkCount * 100 / (size * size) - 50) / 5) * 10;
  return score;
}

export function qr(text, { ecl = 'M' } = {}) {
  if (ecl !== 'M') throw new Error('This local QR encoder supports error correction level M.');
  const bytes = [...new TextEncoder().encode(String(text))];
  const version = Object.keys(BLOCKS_M).map(Number).find(candidate => {
    const dataCapacity = BLOCKS_M[candidate].reduce((total, block) => total + block.count * block.data, 0);
    const countBits = candidate < 10 ? 8 : 16;
    return 4 + countBits + bytes.length * 8 <= dataCapacity * 8;
  });
  if (!version) throw new Error('QR link is too long. Download and send the .egg instead.');
  const codewords = makeCodewords(bytes, version);
  let best = null, bestPenalty = Infinity;
  for (let mask = 0; mask < 8; mask++) {
    const matrix = buildBase(version);
    placeFormat(matrix, mask);
    placeData(matrix, codewords, mask);
    const currentPenalty = penalty(matrix);
    if (currentPenalty < bestPenalty) {
      best = matrix;
      bestPenalty = currentPenalty;
    }
  }
  return { size: best.length, modules: best };
}
