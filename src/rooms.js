// Room centers remain stable for movement-based room detection and the floor plan.
// Shortcuts land just inside each entrance; open living/dining zones use their approach edge.
export const rooms=[
  {name:'玄关',x:4.65,z:5.9,look:[6.4,4.7],entry:{x:4.6,z:6.78,look:[5.65,5.25]}},
  {name:'客厅',x:11.7,z:5.1,look:[8,4.8],entry:{x:9.85,z:5.15,look:[11.7,5.65]}},
  {name:'餐厅',shortcut:false,x:7.65,z:5.4,look:[6.4,4.7],entry:{x:6.3,z:5.55,look:[7,4.85]}},
  {name:'厨房',x:6.2,z:2.65,look:[6.35,.7],entry:{x:5.65,z:2.65,look:[6.2,1.3]}},
  {name:'主卧',x:12.45,z:2.7,look:[11.3,1.5],entry:{x:13.5,z:3.7,look:[13.35,1.85]}},
  {name:'次卧',x:2.65,z:3,look:[1.1,2.4],entry:{x:4.1,z:3.9,look:[1.4,3.2]}},
  {name:'儿童房',x:2.25,z:5.75,look:[1,5.2],entry:{x:3.05,z:5.05,look:[1.3,5.75]}},
  {name:'主卫',x:8.95,z:2.3,look:[8.3,1.1],entry:{x:10.1,z:2.5,look:[8.2,2.25]}},
  {name:'次卫',x:4.75,z:1.6,look:[4.9,.6],entry:{x:4.9,z:2.69,look:[4.75,.65]}},
];
