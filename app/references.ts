export const REFERENCES = [
  {id:'male', label:'Male', file:'/models/atlas.json', source:'BodyParts3D', caption:'ADULT HUMAN · MALE'},
  {id:'female', label:'Female', file:'/models/atlas-female-expanded.json', source:'Denver + NLM + HRA', caption:'FEMALE ASSEMBLY · EXPERIMENTAL'},
  {id:'infant', label:'Infant', file:'/models/atlas-infant-expanded.json', source:'dHCP + Tyndall', caption:'INFANT · BRAIN & CHEST'},
] as const;
export type ReferenceId = typeof REFERENCES[number]['id'];

export function referenceFromSearch(search:string):ReferenceId {
  const params=new URLSearchParams(search);
  if(params.get('model')==='infant-thorax'||params.get('source')==='tyndall-newborn-thorax')return 'infant';
  if(params.get('model')==='infant'||params.get('sex')==='infant'||params.get('source')==='dhcp-neonatal')return 'infant';
  if(params.get('sex')==='female')return 'female';
  if(params.get('sex')==='male'||params.get('source')==='bodyparts3d')return 'male';
  return ['composed','hra-female','denver-vhf','nlm-vhf-ct','tcia'].includes(params.get('source')??'')?'female':'male';
}

export function referenceUrl(href:string,id:ReferenceId) {
  const url=new URL(href);
  if(id==='infant'){url.searchParams.set('model',id);url.searchParams.delete('sex');}
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

export const INFANT_SOURCE = {label:'Developing Human Connectome Project',url:'https://gin.g-node.org/BioMedIA/dhcp-volumetric-atlas-groupwise',description:'85 brain regions from a mixed-sex neonatal population atlas at 40 weeks post-menstrual age. Resized and placed above the chest in the combined infant view; proportions and alignment are approximate.'};

export const INFANT_THORAX_SOURCE = {label:'Tyndall / Cork University Hospital · Newborn chest',url:'https://zenodo.org/records/4916863',description:'Nine chest organ and tissue regions from a published newborn CT-derived mesh. The infant was born at 36 weeks gestation; age at the scan and sex are not reported. Combined with the dHCP brain for display; the sources represent different infants.'};

export const FEMALE_GAPS = [
  'Complete forearm boundaries and individually labeled hand bones; current CT references are partial or grouped.',
  'Most upper-body, arm and hand muscles.',
  'Full coverage of small nerves, vessels and connective tissues.',
  'A whole-body skin surface in the expanded assembly.',
];
