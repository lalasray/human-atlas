import {ArrowUpRight} from 'lucide-react';
import type {Atlas,Part} from './anatomy';
import {FEMALE_GAPS,FEMALE_SOURCES,INFANT_SOURCE,type ReferenceId} from './references';

export function PartSources({parts,expanded}:{parts:Part[];expanded:boolean}) {
  const sources=[...new Set(parts.flatMap(p=>p.provenance?[p.provenance.source]:[]))];
  if(!sources.length)return <a className="source-link" href="https://lifesciencedb.jp/bp3d/" target="_blank" rel="noreferrer">View anatomical source <ArrowUpRight size={14}/></a>;
  return <div className="part-sources"><h3>Source anatomy</h3>{sources.map(id=>{
    const source=id==='dhcp-neonatal'?INFANT_SOURCE:FEMALE_SOURCES[id];
    return source?<div key={id}><a className="source-link" href={source.url} target="_blank" rel="noreferrer">{source.label} <ArrowUpRight size={14}/></a><p>{source.description}</p></div>:null;
  })}{expanded&&<p className="context-note">Combined placement is experimental and has not had anatomical review.</p>}</div>;
}

export function AtlasSources({atlas,reference}:{atlas:Atlas|null;reference:ReferenceId}) {
  const female=reference==='female';
  if(reference==='infant')return <div className="about-copy">
    <p><strong>Infant · Neonatal brain</strong><br/>{atlas?.parts.length??'…'} brain regions at 40 weeks post-menstrual age, around the expected time of birth. This is a population reference derived from 275 structurally normal neonatal MRI scans, including both sexes.</p>
    <h3>Current coverage</h3><p>The brain includes cortical regions, white matter, deep brain structures, brainstem and ventricular regions. The source labels are retained; two background labels are excluded.</p>
    <h3>Still missing</h3><p>Skull, face, eyes, ears, body skeleton, muscles, internal organs, peripheral vessels, nerves and skin are not included. This is not a whole-body infant model.</p>
    <p>The geometry keeps its original metric scale, with a display rotation and translation. It is not registered to an adult body. Local mesh conversion and anatomical labels remain unreviewed.</p>
    <h3>Credits</h3><p>Schuh et al., Developing Human Connectome Project, unbiased construction of a spatio-temporal atlas of the neonatal brain. CC BY 4.0. Converted from the 40-week Draw-EM segmentation, simplified, and reoriented for display.</p>
    <a href={INFANT_SOURCE.url} target="_blank" rel="noreferrer">dHCP source atlas <ArrowUpRight size={14}/></a>
    <a href="https://doi.org/10.1101/251512" target="_blank" rel="noreferrer">Atlas publication <ArrowUpRight size={14}/></a>
    <a href="/infant-sources/coverage.json" target="_blank" rel="noreferrer">Coverage and import evidence <ArrowUpRight size={14}/></a>
    <a href="/infant-sources/LICENSE.md" target="_blank" rel="noreferrer">Source license <ArrowUpRight size={14}/></a>
  </div>;
  const sources=Object.entries(FEMALE_SOURCES).filter(([id])=>atlas?.parts.some(p=>p.provenance?.source===id));
  return <div className="about-copy">
    <p><strong>{female?'Female · Expanded assembly':'Male · BodyParts3D'}</strong><br/>{atlas?.parts.length.toLocaleString()??'…'} meshes and {atlas?.concepts.length.toLocaleString()??'…'} named concepts. Some meshes group several anatomical structures.</p>
    {female?<>
      <p>Expanded with 128 Denver lower-limb meshes, 101 TotalSegmentator CT labels and 10 MOOSE hand/forearm labels from the same Visible Human Female donor. These are combined with 786 HRA detail meshes.</p>
      <p>New hand meshes group the carpal, metacarpal and finger bones on each side. Radius and ulna references are partial because the source scan cuts off parts of the arms; the right ulna is fragmented.</p>
      <h3>Included sources</h3>
      <table className="source-table"><thead><tr><th>Source</th><th>Meshes</th></tr></thead><tbody>{sources.map(([id,source])=><tr key={id}><td>{source.label}</td><td>{atlas?.parts.filter(p=>p.provenance?.source===id).length}</td></tr>)}</tbody></table>
      <h3>Remaining gaps</h3><ul>{FEMALE_GAPS.map(gap=><li key={gap}>{gap}</li>)}</ul>
      <p>The assembly is incomplete. CT boundaries are automatic, and the HRA organ alignment is experimental. Passing geometry checks does not establish anatomical accuracy.</p>
      <a href="/female-sources/coverage.json" target="_blank" rel="noreferrer">Coverage counts and import record <ArrowUpRight size={14}/></a>
      <a href="/female-sources/generated/registration-report.json" target="_blank" rel="noreferrer">Alignment evidence <ArrowUpRight size={14}/></a>
      <a href="/female-sources/hand-forearm-qa.json" target="_blank" rel="noreferrer">Hand and forearm conversion record <ArrowUpRight size={14}/></a>
    </>:null}
    {female&&<p>Eight placenta and umbilical structures appear under Pregnancy reference and are hidden by default.</p>}
    <p>Colors, system groupings and short explanations provide general educational context. This reference does not contain every human structure or variation and is not a diagnostic or surgical tool.</p>
    <h3>Credits</h3>
    {female?<>
      <p>Kristen Browne and Heidi Schlehlein, Human Reference Atlas / HuBMAP, 3D Reference Organ Set for Female v1.5 (2023). CC BY 4.0.</p>
      <p>Andreassen et al., University of Denver Center for Orthopaedic Biomechanics, Visible Human Female lower-limb geometry (2022). CC BY 4.0.</p><p>Courtesy of the U.S. National Library of Medicine. CT-derived meshes were produced by the source repository using TotalSegmentator and do not reflect the most current or accurate NLM data. NLM does not endorse this application.</p><a href="https://www.nlm.nih.gov/databases/download/terms_and_conditions.html" target="_blank" rel="noreferrer">NLM terms and conditions <ArrowUpRight size={14}/></a>
      <p>The additional hand/forearm meshes were segmented locally with MOOSE 3.2.2 by ENHANCE-PET. The model weights are CC BY 4.0; the source CT remains subject to NLM terms. Automatic left/right correction and removal of a two-voxel fragment are recorded with the geometry.</p>
      {sources.map(([id,source])=><a key={id} href={source.url} target="_blank" rel="noreferrer">{source.label} <ArrowUpRight size={14}/></a>)}
      <a href="https://github.com/rubdttcom/human-atlas" target="_blank" rel="noreferrer">Female Open Human Atlas repository <ArrowUpRight size={14}/></a>
    </>:<>
      <p>BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International.</p>
      <a href="https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html" target="_blank" rel="noreferrer">Dataset license <ArrowUpRight size={14}/></a>
      <a href="https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html" target="_blank" rel="noreferrer">Original geometry & metadata <ArrowUpRight size={14}/></a>
    </>}
    <a href="/ATTRIBUTION.md" target="_blank" rel="noreferrer">Full attribution & adaptations <ArrowUpRight size={14}/></a>
  </div>;
}
