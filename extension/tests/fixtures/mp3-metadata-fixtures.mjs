// Original synthetic MPEG headers. No owner audio is stored in this fixture.
export const join = (...parts) => Buffer.concat(parts.map(p => Buffer.from(p)));
export const text = value => Buffer.from(value, 'utf8');
export function frames(count = 60) {
  const audio = Buffer.alloc(count * 417);
  for (let p = 0; p < audio.length; p += 417) audio.set([255, 251, 144, 100], p);
  return audio;
}
export function lyrics2(fields = [['IND', '10'], ['LYR', '']]) {
  const body = join(text('LYRICSBEGIN'), ...fields.map(([id, value]) => {
    const bytes = text(value);
    return join(text(id + String(bytes.length).padStart(5, '0')), bytes);
  }));
  return join(body, text(String(body.length).padStart(6, '0') + 'LYRICS200'));
}
export const lyrics1 = value => text('LYRICSBEGIN' + value + 'LYRICSEND');
export function id3v1(genre = 0) { const tag = Buffer.alloc(128); tag.write('TAG'); tag[127] = genre; return tag; }
export function id3v2(footer = false) {
  const body = text('synthetic tag body');
  const head = Buffer.from([73,68,51,4,0,footer?16:0,0,0,0,body.length]);
  const foot = Buffer.from(head); foot.write('3DI');
  return join(head, body, footer ? foot : Buffer.alloc(0));
}
export function ape(version = 2000, header = false) {
  const item = join(Buffer.from([4,0,0,0,0,0,0,0]), text('Title\0Test'));
  const footer = Buffer.alloc(32); footer.write('APETAGEX');
  footer.writeUInt32LE(version, 8); footer.writeUInt32LE(item.length + 32, 12); footer.writeUInt32LE(1, 16);
  if (header) footer.writeUInt32LE(0x80000000, 20);
  const head = Buffer.from(footer); head.writeUInt32LE(0xa0000000, 20);
  return join(header ? head : Buffer.alloc(0), item, footer);
}
export function metadataCases() {
  const audio = frames(), info = frames(1); info.write('Info', 36);
  const enhanced = Buffer.alloc(227); enhanced.write('TAG+');
  const xmp = text('ABCDEF0123456" stRef:documentID="xmp.did:0123456789ABCDEF"/> </rdf:Description> </rdf:RDF> </x:xmpmeta>');
  const pass = (name, source, expected = audio) => ({name, source, expected});
  const fail = (name, source) => ({name, source, expected: null});
  const cases = [
    pass('plain frames', audio),
    pass('Lyrics3v2 actual empty lyrics layout', join(audio, lyrics2(), id3v1())),
    pass('Lyrics3v2 UTF8 lyrics and unknown uppercase field', join(audio, lyrics2([['LYR','Строка\r\n[00:01]Текст'],['XYZ','extension field']]))),
    pass('Lyrics3v1', join(audio, lyrics1('Text\r\nAnother line'), id3v1(7))),
    pass('APEv1', join(audio, ape(1000))),
    pass('APEv2 footer', join(audio, ape())),
    pass('APEv2 header and footer', join(audio, ape(2000, true))),
    pass('enhanced ID3v1', join(audio, enhanced, id3v1())),
    pass('tail ID3v2', join(audio, id3v2())),
    pass('tail ID3v2 with footer', join(audio, id3v2(true))),
    pass('mixed reverse tag ordering', join(audio, lyrics2(), id3v1(), ape(), lyrics1('lyrics'), id3v1())),
    pass('padding beyond zero genre', join(audio, lyrics2(), id3v1(), Buffer.alloc(257))),
    pass('padding between metadata tags', join(audio, lyrics2(), Buffer.alloc(17), ape(), Buffer.alloc(11), id3v1(), Buffer.alloc(8))),
    pass('repeated tags', join(audio, lyrics2(), lyrics2(), id3v1(), id3v1())),
    pass('leading tags and duplicate Info', join(id3v2(),info,id3v2(),info,audio,lyrics2(),id3v1()),join(info,audio)),
    pass('orphan XMP compatibility', join(audio,Buffer.alloc(64),xmp,id3v1())),
    pass('outer padding beyond XMP', join(audio,Buffer.alloc(64),xmp,Buffer.alloc(17))),
    pass('UTF8 inflated ID3v1', join(audio,text('TAG'+'Ж'.repeat(27)+'x'.repeat(97)),Buffer.from([7]))),
    fail('arbitrary tail', join(audio, text('unrecognized trailer'))),
    fail('truncated audio', audio.subarray(0,-20)),
    fail('internal broken MPEG header', join(audio.subarray(0,417),Buffer.from([1]),audio.subarray(417),lyrics2())),
    fail('unknown bytes before valid tag', join(audio,text('junk'),lyrics2())),
    fail('wrong Lyrics3v2 total size', join(audio,text('LYRICSBEGINLYR00000'+'000018LYRICS200'))),
    fail('wrong Lyrics3v2 field size', join(audio,lyrics2([['LYR','hello']]).map((c,i)=>i===18?57:c))),
    fail('truncated Lyrics3v2 footer', join(audio,lyrics2().subarray(0,-1))),
    fail('truncated Lyrics3v1 begin', join(audio,text('YRICSBEGINtextLYRICSEND'))),
    fail('binary Lyrics3v1', join(audio,lyrics1('text\0binary'))),
    fail('invalid APE version', join(audio,ape(1234))),
    fail('APE size crosses audio', join(audio,(()=>{const tag=ape();tag.writeUInt32LE(999999,tag.length-20);return tag;})())),
    fail('excess metadata tags', join(audio,...Array.from({length:17},()=>id3v1()))),
    fail('excess padding', join(audio,Buffer.alloc(4097))),
    fail('bad ID3 synchsafe size', join(audio,Buffer.from([73,68,51,4,0,0,128,0,0,0]))),
    fail('invalid ID3 footer', join(audio,(()=>{const tag=id3v2(true);tag[tag.length-10]=88;return tag;})())),
    fail('binary XMP', join(audio,Buffer.alloc(64),text(xmp.toString().replace('stRef:', 'st\0Ref:')))),
  ];
  // A single missing ancillary slot is the only retained EOF repair.
  const last=Buffer.alloc(1045,0xaa);last.fill(0,0,36);last.set([255,251,226,100]);
  last[6]=4; // part2_3_length = 1024 bits at side-info bit offset 20.
  cases.push(pass('one missing ancillary byte',join(audio,last.subarray(0,-1)),join(audio,last.subarray(0,-1),Buffer.alloc(1))));
  return cases;
}
