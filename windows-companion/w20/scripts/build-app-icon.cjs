// Bundle the EXISTING CELIKOM extension "C" mark into the native Windows
// executable, Inno Setup installer and taskbar/tray. Never draw a new logo.
// Input assets are committed under extension/assets/icons/green-{size}.png.
"use strict";
const fs = require("node:fs");
const path = require("node:path");

const assets = path.resolve(__dirname, "../../../extension/assets/icons");
const output = path.resolve(__dirname, "../assets/CELIKOM.ico");
const sizes = [16, 32, 48, 128];
const entries = sizes.map(size => {
  const png = fs.readFileSync(path.join(assets, `green-${size}.png`));
  if (png.subarray(0, 8).toString("hex") !== "89504e470d0a1a0a" ||
      png.toString("ascii", 12, 16) !== "IHDR" ||
      png.readUInt32BE(16) !== size || png.readUInt32BE(20) !== size) {
    throw Error(`W66_ICON_SOURCE_INVALID_${size}`);
  }
  return {size, png};
});

const directory = Buffer.alloc(6 + entries.length * 16);
directory.writeUInt16LE(0, 0);
directory.writeUInt16LE(1, 2); // ICO: 1
directory.writeUInt16LE(entries.length, 4);
let offset = directory.length;
entries.forEach(({size, png}, index) => {
  const pos = 6 + index * 16;
  directory[pos] = size === 256 ? 0 : size;
  directory[pos + 1] = size === 256 ? 0 : size;
  directory[pos + 2] = 0; // original image palette
  directory[pos + 3] = 0;
  directory.writeUInt16LE(1, pos + 4);
  directory.writeUInt16LE(32, pos + 6);
  directory.writeUInt32LE(png.length, pos + 8);
  directory.writeUInt32LE(offset, pos + 12);
  offset += png.length;
});
const icon = Buffer.concat([directory, ...entries.map(e => e.png)]);
fs.mkdirSync(path.dirname(output), {recursive: true});
fs.writeFileSync(output, icon);
console.log(`W66_BRAND_ICON_BUILT sizes=${sizes.join(",")} bytes=${icon.length}`);
