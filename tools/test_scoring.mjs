// Kiểm tra logic chấm Reading và làm tròn band trong web/index.html. Chạy: node tools/test_scoring.mjs
import {readFileSync} from 'node:fs';
const src = readFileSync(new URL('../web/index.html', import.meta.url), 'utf8');
const grab = name => { const m = src.match(new RegExp(`^const ${name} = [\\s\\S]*?;\\n(?=const |function |/\\*|let )`, 'm')); if (!m) throw new Error('không thấy ' + name); return m[0]; };
const code = ['RL_TABLE', 'rlBand', 'half', 'RL_ALIAS', 'normAns', 'isRight'].map(grab).join('\n');
const {rlBand, half, isRight} = new Function(code + '\nreturn {rlBand, half, isRight};')();
const eq = (a, b, msg) => { if (a !== b) throw new Error(`${msg}: ${a} !== ${b}`); };
eq(rlBand('reading', 30), 7, 'R 30'); eq(rlBand('reading', 29), 6.5, 'R 29'); eq(rlBand('reading', 32), 7, 'R 32');
eq(rlBand('reading', 33), 7.5, 'R 33'); eq(rlBand('reading', 40), 9, 'R 40'); eq(rlBand('reading', 2), 1, 'R 2'); eq(rlBand('reading', 0), 0, 'R 0');
eq(half(6.25), 6.5, '.25 lên .5'); eq(half(6.75), 7, '.75 lên 1'); eq(half(6.125), 6, '.125 xuống'); eq(half(6.625), 6.5, '.625 xuống .5');
eq(isRight('T', 'TRUE'), true, 'T = TRUE'); eq(isRight('ng', 'NOT GIVEN'), true, 'ng'); eq(isRight(' Library. ', 'library'), true, 'trim/dấu chấm');
eq(isRight('libraries', 'library'), false, 'số nhiều khác'); eq(isRight('15th May', 'May 15th / 15th May'), true, 'nhiều đáp án'); eq(isRight('', 'a'), false, 'bỏ trống');
eq(isRight('false', 'TRUE'), false, 'sai');
console.log('scoring OK');
