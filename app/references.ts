export const REFERENCES = [
  {id:'male', label:'Male · BodyParts3D', file:'/models/atlas.json', source:'BodyParts3D', caption:'ADULT HUMAN · MALE'},
  {id:'female', label:'Female · Expanded', file:'/models/atlas-female-expanded.json', source:'Denver + NLM + HRA', caption:'FEMALE ASSEMBLY · EXPERIMENTAL'},
  {id:'infant', label:'Infant · Brain', file:'/models/atlas-infant.json', source:'dHCP · 40 weeks PMA', caption:'NEONATAL BRAIN · 40 WEEKS PMA'},
] as const;
export type ReferenceId = typeof REFERENCES[number]['id'];

export function referenceFromSearch(search:string):ReferenceId {
  const params=new URLSearchParams(search);
  if(params.get('model')==='infant'||params.get('sex')==='infant'||params.get('source')==='dhcp-neonatal')return 'infant';
  if(params.get('sex')==='female')return 'female';
  if(params.get('sex')==='male'||params.get('source')==='bodyparts3d')return 'male';
  return ['composed','hra-female','denver-vhf','nlm-vhf-ct','tcia'].includes(params.get('source')??'')?'female':'male';
}

export function referenceUrl(href:string,id:ReferenceId) {
  const url=new URL(href);
  if(id==='infant'){url.searchParams.set('model','infant');url.searchParams.delete('sex');}
  else{url.searchParams.set('sex',id);url.searchParams.delete('model');}
  url.searchParams.delete('reference');
  url.searchParams.delete('source');
  return url;
}

export const FEMALE_SOURCES:Record<string,{label:string;url:string;description:string}> = {
  'hra-female':{label:'Human Reference Atlas',url:'https://lod.humanatlas.io/ref-organ/united-female/v1.5',description:'Reference assembly; individual component donors unresolved.'},
  'denver-vhf':{label:'University of Denver · VHF',url:'https://digitalcommons.du.edu/visiblehuman/1/',description:'Visible Human Female donor; manually segmented lower limb, smoothed by the source.'},
  'nlm-vhf-ct':{label:'NLM Visible Human Female · CT',url:'https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Female-Images/radiological/normalCT/',description:'Same female donor as Denver; automatic TotalSegmentator labels, unreviewed.'},
  'nlm-vhf-moose':{label:'NLM Visible Human Female · MOOSE bones',url:'https://github.com/ENHANCE-PET/MOOSE',description:'Ten automatic hand/forearm labels from the same female CT. Hand bones are grouped; forearms are partial where the scan cuts off the arms. Anatomically unreviewed.'},
};

export const INFANT_SOURCE = {label:'Developing Human Connectome Project',url:'https://gin.g-node.org/BioMedIA/dhcp-volumetric-atlas-groupwise',description:'85 brain regions from a mixed-sex neonatal population atlas at 40 weeks post-menstrual age. Brain only; local mesh conversion unreviewed.'};

export const FEMALE_GAPS = [
  'Complete forearm boundaries and individually labeled hand bones; current CT references are partial or grouped.',
  'Most upper-body, arm and hand muscles.',
  'Full coverage of small nerves, vessels and connective tissues.',
  'A whole-body skin surface in the expanded assembly.',
];
