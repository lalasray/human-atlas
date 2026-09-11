import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {gunzipSync} from 'node:zlib';

const filename=process.argv[2]??'atlas.json';
const base=new URL('../public/models/',import.meta.url);
const manifest=fs.readFileSync(new URL(filename,base)),atlas=JSON.parse(manifest);
const expected={
  'atlas.json':{parts:2234,concepts:3432},
  'atlas-female-expanded.json':{parts:1025,concepts:943},
  'atlas-female.json':{parts:888,concepts:1073},
  'atlas-tcia-female.json':{parts:36,concepts:36},
  'atlas-denver-female.json':{parts:128,concepts:203},
  'atlas-nlm-vhf-ct.json':{parts:114,concepts:148},
  'atlas-dhcp-neonatal.json':{parts:85,concepts:85},
  'atlas-infant.json':{parts:85,concepts:85},
  'atlas-infant-thorax.json':{parts:9,concepts:9},
  'atlas-infant-expanded.json':{parts:94,concepts:94},
}[filename];
assert.ok(expected,'Unknown atlas fixture');
assert.equal(atlas.parts.length,expected.parts);
assert.equal(atlas.concepts.length,expected.concepts);
const systems=new Set(['skeletal','muscular','cardiac','sensory','arterial','venous','nervous','respiratory','digestive','urinary','lymphatic','endocrine','reproductive','integumentary','connective','pregnancy','tissue']);
const ids=new Set(atlas.parts.map(p=>p.id));assert.equal(ids.size,expected.parts);
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const files=atlas.chunks.map(c=>{
  const b=fs.readFileSync(new URL(c.url.split('/').pop(),base));
  assert.equal(b.length,c.bytes);
  if(c.sha256)assert.equal(hash(b),c.sha256);
  if(c.gzip){
    const gz=fs.readFileSync(new URL(c.gzip.split('/').pop(),base));
    assert.equal(gz.length,c.gzipBytes);assert.deepEqual(gunzipSync(gz),b);
  }
  return b;
});
let tris=0;
for(const p of atlas.parts){
  assert.ok(p.name.trim()&&p.name!=='-'&&!p.name.includes('Bounds('));
  assert.ok(p.conceptId&&p.conceptId!=='-');assert.ok(systems.has(p.system));
  const b=files[p.chunk];assert.ok(b,`${p.id}: missing chunk`);
  for(const [offset,count,bytes] of [[p.positions,p.vertexCount*3,4],[p.normals,p.vertexCount*3,2],[p.indices,p.indexCount,4]]){
    assert.ok(Number.isInteger(offset)&&offset>=0&&offset%bytes===0);
    assert.ok(Number.isInteger(count)&&count>0&&offset+count*bytes<=b.length);
  }
  const pos=new Float32Array(b.buffer,b.byteOffset+p.positions,p.vertexCount*3);
  const indices=new Uint32Array(b.buffer,b.byteOffset+p.indices,p.indexCount);
  assert.ok(indices.length>=3&&indices.length%3===0);
  for(const i of indices)assert.ok(i<p.vertexCount,`${p.id}: invalid vertex`);
  const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
  for(let i=0;i<pos.length;i++){
    const value=pos[i],axis=i%3;assert.ok(Number.isFinite(value));
    min[axis]=Math.min(min[axis],value);max[axis]=Math.max(max[axis],value);
  }
  for(let axis=0;axis<3;axis++){
    // Original atlases keep conservative pre-simplification bounds.
    assert.ok(Number.isFinite(p.bounds[0][axis])&&Number.isFinite(p.bounds[1][axis]));
    assert.ok(p.bounds[0][axis]<=p.bounds[1][axis]);
    assert.ok(min[axis]>=p.bounds[0][axis]-1e-6,`${p.id}: vertex below minimum bounds`);
    assert.ok(max[axis]<=p.bounds[1][axis]+1e-6,`${p.id}: vertex above maximum bounds`);
  }
  tris+=p.indexCount/3;
}
assert.equal(new Set(atlas.concepts.map(c=>c.id)).size,atlas.concepts.length);
for(const c of atlas.concepts){
  assert.ok(c.elements.length);
  for(const id of c.elements)assert.ok(ids.has(id),`${c.id}: missing ${id}`);
}
assert.equal(tris,atlas.triangles);
if(filename==='atlas-female-expanded.json'){
  assert.equal(atlas.parts.filter(p=>p.system==='pregnancy').length,8);
  assert.equal(atlas.parts.filter(p=>p.system==='reproductive').length,38);
  for(const p of atlas.parts)assert.ok(p.provenance&&p.provenance.source!=='bodyparts3d');
}
if(filename==='atlas-infant.json'){
  const report=JSON.parse(fs.readFileSync(new URL('../infant-sources/coverage.json',base)));
  assert.equal(hash(manifest),report.manifestSha256);
  assert.equal(atlas.region,'brain');
  assert.equal(atlas.display_transform.scale,1);
  assert.equal(atlas.display_transform.registration_to_adult,false);
  assert.equal(atlas.source_revision,'d699540b1820d8224a07db3c1d727d0c747218dc');
  const labels=new Set();
  for(const part of atlas.parts){
    const p=part.provenance;
    assert.equal(part.system,'nervous');assert.equal(p.source,'dhcp-neonatal');
    assert.equal(p.source_sex,'mixed-aggregate');assert.equal(p.source_donor,'dhcp-ga40-aggregate');
    assert.equal(p.license,'CC-BY-4.0');assert.equal(p.reference_age,'40 weeks post-menstrual age');
    assert.equal(p.derived_chunk_sha256,atlas.chunks[part.chunk].sha256);
    assert.ok(part.bounds[0][1]>=.00999&&part.bounds[1][1]<.3,'Infant metric scale/floor changed');
    labels.add(p.label_value);
  }
  assert.equal(labels.size,85);assert.ok(!labels.has(84)&&!labels.has(85));
}
if(filename==='atlas-infant-thorax.json'){
  const report=JSON.parse(fs.readFileSync(new URL('../infant-sources/thorax/coverage.json',base)));
  assert.equal(hash(manifest),report.manifestSha256);
  assert.equal(atlas.region,'thorax');assert.equal(atlas.license,'CC-BY-4.0');
  assert.equal(atlas.input_sha256,'7de29df4092f47f702b7a27d0c6c3e147f953dcc6db8d8bc3ddda7fd4d9e77a3');
  assert.equal(atlas.gestational_age_at_birth_weeks,36);assert.equal(atlas.age_at_scan,'not reported');
  assert.equal(atlas.population_sex,'not reported');assert.equal(atlas.sex,undefined);
  assert.equal(atlas.display_transform.scale,1);
  assert.equal(atlas.display_transform.registration_to_brain,false);assert.equal(atlas.display_transform.registration_to_adult,false);
  assert.equal(report.sourceNodes,229363);assert.equal(report.sourceTetrahedra,1356069);
  assert.equal(report.triangles,atlas.triangles);assert.equal(report.geometrySha256,atlas.chunks[0].sha256);
  const mapping={lungs:['respiratory',[1,10,11]],bone:['skeletal',[2]],cartilage:['connective',[3]],heart:['cardiac',[4]],muscle:['muscular',[5]],artery:['arterial',[6]],fat:['tissue',[7]],skin:['integumentary',[8]],trachea:['respiratory',[9]]};
  const labels=[];
  for(const part of atlas.parts){
    const p=part.provenance,[system,regions]=mapping[p.source_asset];
    assert.equal(p.source,'tyndall-newborn-thorax');assert.equal(p.source_donor,'CUH-newborn-thorax-4916863');
    assert.equal(p.license,'CC-BY-4.0');assert.equal(p.canonical_space,null);assert.equal(p.registration.transform_id,null);
    assert.equal(part.system,system);assert.deepEqual(p.source_region_ids,regions);labels.push(...regions);
    assert.equal(p.derived_chunk_sha256,atlas.chunks[part.chunk].sha256);
    assert.ok(part.bounds[0][1]>=.00999&&part.bounds[1][1]<.12,'Chest metric scale/floor changed');
    assert.ok(part.bounds[0][0]>-.07&&part.bounds[1][0]<.07,'Chest width changed');
    const row=report.regions.find(r=>r.id===part.id);assert.ok(row);assert.equal(row.triangles,part.indexCount/3);
  }
  assert.deepEqual(labels.sort((a,b)=>a-b),Array.from({length:11},(_,i)=>i+1));
  assert.ok(!atlas.default_visible.includes('muscular')&&!atlas.default_visible.includes('tissue')&&!atlas.default_visible.includes('integumentary'));
}
if(filename==='atlas-infant-expanded.json'){
  const report=JSON.parse(fs.readFileSync(new URL('../infant-sources/assembly.json',base)));
  assert.equal(hash(manifest),report.manifestSha256);
  assert.equal(atlas.region,'infant-assembly');assert.equal(atlas.assembly.anatomical_registration,false);
  assert.equal(atlas.assembly.shared_donor,false);assert.equal(atlas.assembly.complete_body,false);
  assert.deepEqual(atlas.display_transforms,report.displayTransforms);
  const brain=atlas.parts.filter(p=>p.provenance.source==='dhcp-neonatal');
  const chest=atlas.parts.filter(p=>p.provenance.source==='tyndall-newborn-thorax');
  assert.equal(brain.length,85);assert.equal(chest.length,9);
  const bounds=parts=>[0,1].map(side=>[0,1,2].map(axis=>(side?Math.max:Math.min)(...parts.map(p=>p.bounds[side][axis]))));
  const [bl,bh]=bounds(brain),[cl,ch]=bounds(chest);
  assert.ok(Math.abs((bh[0]-bl[0])/(ch[0]-cl[0])-.78)<1e-6);
  assert.ok(Math.abs(bl[1]-ch[1]-atlas.assembly.brain_chest_gap_m)<1e-6,'Brain must sit above chest');
  assert.ok(atlas.default_visible.includes('nervous')&&atlas.default_visible.includes('cardiac'));
  for(const transform of atlas.display_transforms){
    const sourceBytes=fs.readFileSync(new URL(transform.source_manifest.split('/').pop(),base));
    assert.equal(hash(sourceBytes),transform.source_manifest_sha256);
    const source=JSON.parse(sourceBytes),sourceFiles=source.chunks.map(c=>fs.readFileSync(new URL(c.url.split('/').pop(),base)));
    for(const original of source.parts){
      const part=atlas.parts.find(p=>p.id===original.id);assert.ok(part,'An input part was dropped');
      assert.equal(part.provenance.source_donor,original.provenance.source_donor);
      assert.equal(part.provenance.license,original.provenance.license);
      assert.deepEqual(part.provenance.display_transform,transform);
      assert.equal(part.provenance.derived_chunk_sha256,atlas.chunks[part.chunk].sha256);
      assert.equal(part.vertexCount,original.vertexCount);assert.equal(part.indexCount,original.indexCount);
      const input=sourceFiles[original.chunk],output=files[part.chunk];
      assert.equal(hash(input),part.provenance.assembly_input_chunk_sha256);
      for(const [offset,bytes] of [['normals',part.vertexCount*6],['indices',part.indexCount*4]])
        assert.deepEqual(output.subarray(part[offset],part[offset]+bytes),input.subarray(original[offset],original[offset]+bytes));
      for(let i=0;i<part.vertexCount;i++)for(let axis=0;axis<3;axis++){
        const expected=input.readFloatLE(original.positions+i*12+axis*4)*transform.scale+transform.matrix[axis][3];
        assert.ok(Math.abs(output.readFloatLE(part.positions+i*12+axis*4)-expected)<1e-7,'Display transform mismatch');
      }
    }
  }
}
if(filename==='atlas-female-expanded.json'){
  const report=JSON.parse(fs.readFileSync(new URL('../female-sources/coverage.json',base)));
  const compositionBytes=fs.readFileSync(new URL('../atlases/composed.json',base));
  const composition=JSON.parse(compositionBytes);
  assert.equal(hash(compositionBytes),report.baseManifestSha256);
  assert.deepEqual(atlas.parts.filter(p=>p.provenance.source!=='nlm-vhf-moose'),composition.parts);
  assert.deepEqual(atlas.concepts.filter(c=>!c.id.startsWith('nlm-vhf-moose:')),composition.concepts);
  assert.equal(atlas.concepts.flatMap(c=>c.elements).length,atlas.parts.length,'Every female mesh has one canonical selection');
  assert.equal(hash(manifest),report.manifestSha256);
  assert.equal(report.counts.expandedMeshes,atlas.parts.length);
  assert.equal(report.counts.concepts,atlas.concepts.length);
  assert.equal(report.counts.originalMeshes-report.counts.excludedHraMeshes+report.counts.addedVhfMeshes,atlas.parts.length);
  for(const row of report.systems)assert.equal(row.expanded,atlas.parts.filter(p=>p.system===row.id).length);
  const sources={};
  for(const p of atlas.parts){
    const record=p.provenance;sources[record.source]=(sources[record.source]??0)+1;
    assert.equal(record.canonical_space,'VHF-image-2022');
    assert.equal(record.derived_chunk_sha256,atlas.chunks[p.chunk].sha256);
    if(record.source!=='hra-female')assert.equal(record.source_donor,'VHF');
    assert.ok(record.registration.transform_id);
  }
  assert.deepEqual(sources,{'hra-female':786,'nlm-vhf-ct':101,'denver-vhf':128,'nlm-vhf-moose':10});
  assert.deepEqual(sources,report.meshesBySource);
  const labels=new Set(atlas.parts.filter(p=>p.provenance.source==='nlm-vhf-ct').map(p=>p.provenance.label_name));
  for(const label of ['skull','rib_left_1','rib_right_12','vertebrae_C1','humerus_left','thyroid_gland'])assert.ok(labels.has(label),label);
  for(const replaced of ['hip_left','hip_right','sacrum','femur_left','femur_right','gluteus_maximus_left','iliopsoas_right'])assert.ok(!labels.has(replaced),`Duplicate CT label: ${replaced}`);
  assert.equal(atlas.parts.filter(p=>p.provenance.source==='denver-vhf'&&p.system==='muscular').length,76);
  const added=atlas.parts.filter(p=>p.provenance.source==='nlm-vhf-moose');
  for(const kind of ['carpal','metacarpal','fingers','radius','ulna'])for(const side of ['left','right']){
    const part=added.find(p=>p.provenance.label_name===`${kind}_${side}`);assert.ok(part);
    assert.equal(part.system,'skeletal');assert.equal(part.provenance.source_sex,'female');
    if(side==='left')assert.ok(part.bounds[0][0]>0);else assert.ok(part.bounds[1][0]<0);
    assert.equal(part.provenance.partial_scan_reference,['radius','ulna'].includes(kind));
    assert.equal(part.provenance.granularity,['radius','ulna'].includes(kind)?'individual':'grouped');
  }
}
console.log(`${filename}: verified ${ids.size} meshes, ${atlas.concepts.length} concepts, ${tris.toLocaleString()} triangles, bounds, binary buffers and gzip.`);
