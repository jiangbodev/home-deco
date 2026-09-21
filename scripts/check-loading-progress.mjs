import assert from 'node:assert/strict';
import {createLoadingProgress} from '../src/loading-progress.js';
const events=[],p=createLoadingProgress(state=>events.push(state));
const manifest={modules:{base:{file:'base.glb',bytes:100,textures:['shared.webp']},room:{file:'room.glb',bytes:200,textures:['shared.webp']}},textures:{'shared.webp':50}};
p.plan(manifest,['base','room','missing']);
assert.equal(events.at(-1).total,350); // shared textures counted once, nonexistent modules ignored
p.bytes('base.glb',25);assert.equal(events.at(-1).loaded,25);
p.bytes('base.glb',10);assert.equal(events.at(-1).loaded,25); // late/out-of-order events never regress
p.resourceDone('/assets/shared.webp?v=1');p.resourceDone('/assets/shared.webp');assert.equal(events.at(-1).loaded,75);
p.resourceDone('base.glb');assert.equal(events.at(-1).loaded,150); // cached load without progress events
p.bytes('room.glb',300);assert.equal(events.at(-1).percent,100); // cap bytes at declared resource length
p.preparing();assert.equal(events.at(-1).phase,'prepare');p.complete();
const n=events.length;p.bytes('room.glb',10);p.resourceDone('other-room.glb');assert.equal(events.length,n); // background work cannot reset initial progress
p.plan(manifest,['base']);p.resourceFailed('shared.webp');p.resourceDone('shared.webp');assert.equal(events.at(-1).loaded,0);
console.log('Loading progress: fixed byte denominator, deduplication, monotonic progress, cache completion, phase changes, failures and background isolation passed.');
