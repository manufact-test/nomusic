import test from 'node:test';
import assert from 'node:assert/strict';
import {summarizeHar, bucketSource, mimeBucket} from '../analysis/har-evidence.mjs';
import {parseArgs} from '../analysis/summarize-har.mjs';

const make = ({time=0,url='https://music.yandex.ru/api/get?access_token=SECRET_TOKEN',type='fetch',mime='application/json',status=200,range=false,headers=[]}={}) => ({
  startedDateTime: new Date(Date.UTC(2026,9,20,12,0,0)+time*1000).toISOString(),
  time: 18,
  _resourceType:type,
  request:{method:'GET',url,headers:range?[{name:'Range',value:'bytes=0-1023'}]:headers},
  response:{status,content:{mimeType:mime},headers:[{name:'Set-Cookie',value:'SENSITIVE_COOKIE'}]}
});

const input={log:{version:'1.2',entries:[
  make({time:0}),
  make({time:8,url:'https://music.yandex.ru/proxy?a=SECRET',type:'media',status:206,mime:'audio/mpeg',range:true}),
  make({time:12,url:'https://foo.invalid/creative?id=SECRET',type:'media',mime:'video/mp4'}),
  make({time:16,url:'https://cdn.yandex.net/media/path?sign=SECRET',type:'media',mime:'audio/ogg',range:true,status:206})
]}};

test('unclassified input cannot become a proof of audio-ad removal',()=>{
  const report=summarizeHar(input,{markers:[12],radiusSeconds:5});
  assert.equal(report.schema,'celikom-har-evidence-v1');
  assert.equal(report.decision,'UNKNOWN');
  assert.equal(report.inputEntries,4);
  assert.equal(report.counts.partial206,2);
  assert.equal(report.windows.length,1);
  assert.equal(report.windows[0].markerSecond,12);
  assert.equal(report.windows[0].countedRequests,3);
  assert.equal(report.windows[0].counts.mime.audio,2);
  assert.equal(report.windows[0].counts.mime.video,1);
});

test('output cannot contain PII, identifiers, query strings, cookies or audio URLs',()=>{
  const out=JSON.stringify(summarizeHar(input,{markers:[12]}));
  for(const raw of ['SECRET','TOKEN','access_token','Set-Cookie','music.yandex.ru','foo.invalid','cdn.yandex.net','/proxy','/creative','bytes=0-1023']) {
    assert.equal(out.includes(raw),false,raw);
  }
  assert.equal(out.includes('audio'),true);
});

test('only coarse url and media type families survive',()=>{
  assert.equal(bucketSource('https://music.yandex.ru/secret?q=1'),'music-site');
  assert.equal(bucketSource('https://sub.yandex.net/tracks?sig=1'),'yandex-family');
  assert.equal(bucketSource('https://other.site/private'),'other-host');
  assert.equal(bucketSource('file:///home/secret'),'unknown');
  assert.equal(mimeBucket('audio/mpeg; charset=UTF-8'),'audio');
  assert.equal(mimeBucket('application/vnd.apple.mpegurl'),'hls-manifest');
  assert.equal(mimeBucket('text/html'),'text');
});

test('reject invalid marker, radius, missing HAR entries, extreme entry count',()=>{
  assert.throws(()=>summarizeHar(input,{markers:[-1]}));
  assert.throws(()=>summarizeHar(input,{markers:['NaN']}));
  assert.throws(()=>summarizeHar(input,{radiusSeconds:999}));
  assert.throws(()=>summarizeHar({log:{} }));
  assert.throws(()=>summarizeHar({log:{entries:Array(50001).fill({})}}));
  assert.throws(()=>parseArgs(['input.har','--evil']));
  assert.throws(()=>parseArgs(['input.har','--mark=abc']));
  assert.deepEqual(parseArgs(['e.har','--mark=22','--radius=6']),{input:'e.har',markers:[22],radiusSeconds:6});
});

test('malformed HAR request and response are excluded, no crash',()=>{
  const malformed={log:{entries:[null,{},make({time:1}),{request:{url:'foo'},response:{}}]}};
  const r=summarizeHar(malformed);
  assert.equal(r.parsedEntries,1);
  assert.equal(r.omittedInvalidEntries,3);
});

test('large capture output is bounded, deterministic, and no raw URL escape',()=>{
  const big={log:{entries:Array.from({length:2300},(_,i)=>make({time:i,url:'https://ads.invalid/?secret=AAA',mime:'audio/aac',type:'media'}))}};
  const report=summarizeHar(big,{markers:[10],radiusSeconds:120});
  assert.equal(report.timeline.length,1200);
  assert.equal(report.droppedTimelineEvents,1100);
  assert.equal(report.windows[0].events.length,100);
  assert.equal(report.windows[0].droppedPreviewEvents,31);
  assert.equal(JSON.stringify(report).includes('AAA'),false);
});

test('malformed response headers, null marker and invalid content MIME fail safely',()=>{
  const unsafe={log:{entries:[{...make({time:1}),response:{status:200,headers:{find:'not a function'},content:{mimeType:42}}}]}};
  const report=summarizeHar(unsafe);
  assert.equal(report.parsedEntries,1);
  assert.equal(report.counts.mime.unknown,1);
  for(const value of [null,'',false,true,[],{},'12']) assert.throws(()=>summarizeHar(input,{markers:[value]}));
});

test('large input parsing does not rely on variable argument spreading',()=>{
  const har={log:{entries:Array.from({length:50000},(_,i)=>make({time:i%300}))}};
  const out=summarizeHar(har);
  assert.equal(out.inputEntries,50000);
  assert.equal(out.parsedEntries,50000);
  assert.equal(out.counts.status['200'],50000);
});
