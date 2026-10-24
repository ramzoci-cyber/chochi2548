// Convierte un DWG a DXF (LibreDWG/WASM) y vuelca un resumen JSON del contenido
// Uso: node convertir.mjs entrada.dwg salida_prefijo
import fs from 'node:fs';
import path from 'node:path';
import { LibreDwg, Dwg_File_Type } from '@mlightcad/libredwg-web';
const [, , entrada, pref] = process.argv;
const wasmDir = path.resolve('node_modules/@mlightcad/libredwg-web/wasm') + '/';
const lib = await LibreDwg.create(wasmDir);
const buf = fs.readFileSync(entrada);
const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
let t0 = Date.now();
try {
  const dxf = lib.dwg_write_dxf(ab);
  if (dxf) { fs.writeFileSync(pref + '.dxf', dxf); console.log('DXF', (dxf.length / 1e6).toFixed(1), 'MB en', (Date.now() - t0) / 1000, 's'); }
  else console.log('dwg_write_dxf devolvió null');
} catch (e) { console.log('error DXF:', e.message); }
t0 = Date.now();
const data = lib.dwg_read_data(ab, Dwg_File_Type.DWG);
if (data === undefined) { console.log('no se pudo leer'); process.exit(1); }
console.log('versión', lib.dwg_get_version_type(data), 'codepage', lib.dwg_get_codepage(data));
const { database: db, stats } = lib.convertEx(data);
console.log('convertido en', (Date.now() - t0) / 1000, 's; entidades desconocidas', stats.unknownEntityCount);
const capas = db.tables?.LAYER?.entries?.map(l => ({ name: l.name, color: l.colorIndex, off: l.off, frozen: l.frozen })) || [];
const cuenta = {};
for (const e of db.entities) { const k = (e.layer || '?') + ' | ' + e.type; cuenta[k] = (cuenta[k] || 0) + 1; }
fs.writeFileSync(pref + '_resumen.json', JSON.stringify({ header: { INSUNITS: db.header?.INSUNITS, EXTMIN: db.header?.EXTMIN, EXTMAX: db.header?.EXTMAX, LUNITS: db.header?.LUNITS }, capas, bloques: (db.tables?.BLOCK_RECORD?.entries || []).map(b => b.name).slice(0, 500), cuenta }, (k, v) => typeof v === 'bigint' ? Number(v) : v, 1));
fs.writeFileSync(pref + '_entidades.json', JSON.stringify(db.entities, (k, v) => typeof v === 'bigint' ? Number(v) : v));
const bmp = lib.dwg_bmp(data); if (bmp) fs.writeFileSync(pref + '_miniatura.' + (bmp.type === 6 ? 'png' : 'bmp'), bmp.data);
lib.dwg_free(data);
console.log('entidades', db.entities.length, 'capas', capas.length);
