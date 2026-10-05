## Score: ZZ CLAUDE TEST - L3 NORTH (auto-dim) vs hand-dimensioned LEVEL 3 - NORTH AREA (SOFFIT PLAN)
| category | hand dims | tool dims | recall exact | recall exact+object | precision exact | precision exact+object |
| beam | 61 | 36 | 40% | 90% | 33% | 52% |
| cj | 30 | 37 | 73% | 96% | 51% | 72% |
| column | 9 | 0 | 0% | 66% | - | - |
| generic | 1 | 0 | 100% | 100% | - | - |
| opening | 6 | 0 | 0% | 0% | - | - |
| other | 5 | 0 | 20% | 20% | - | - |
| slab | 69 | 163 | 34% | 78% | 11% | 36% |
| wall | 2 | 19 | 50% | 100% | 26% | 36% |
| ALL | 183 | 255 | 40% | 80% | 21% | 44% |
**Recall** = share of the detailer's dims the tool reproduced. **Precision** = share of the tool's dims a detailer also drew. Exact = same witness lines; object = same object faces, different anchor. Grid-only strings excluded.
### Missed by the tool (35) - hand dims with no counterpart
| hand dim | cat | references | values |
| 14768748 | column | column > grid | 9" |
| 14768771 | column | grid > grid > column | 2'-0 3/8" | 8'-5 1/4" |
| 18652972 | beam | beam > grid | 5'-9 1/8" |
| 18652973 | beam | grid > beam | 7'-10 7/8" |
| 18653042 | beam | grid > beam | 2'-8" |
| 18958203 | slab | slab > wall | 4'-6" |
| 18958423 | beam | column > beam | 5 3/8" |
| 19098486 | cj | grid > cj | 4'-3 1/4" |
| 19098990 | column | cj > column | 4'-9 1/4" |
| 19290562 | beam | wall > beam | 6'-11 1/2" |
| 19323083 | beam | cj > beam | 8'-0 1/2" |
| 19325612 | slab | grid > slab | 12'-1 3/8" |
| 19325619 | slab | slab > column | 3'-4 3/8" |
| 19328438 | slab | wall > slab | 4'-10 1/4" |
| 19328648 | slab | wall > slab | 8'-8" |
| 19351013 | slab | slab > wall | 12'-7 7/8" |
| 19371380 | other | grid > line | 21'-0" |
| 19378398 | other | line > grid | 2'-9" |
| 19378427 | other | grid > line | 15'-0 3/8" |
| 19378434 | other | line > grid | 3'-11 7/8" |
| 19396740 | slab | slab > slab | 3'-9 3/4" |
| 19396765 | slab | slab > grid | 3'-11 1/8" |
| 19396772 | slab | grid > slab | 4'-6 3/4" |
| 19396779 | opening | opening > slab | 1'-5 3/4" |
| 19396804 | opening | slab > opening | 4'-0 3/8" |
| 19396811 | opening | opening > slab | 4'-5 1/8" |
| 19396836 | opening | opening > wall | 4'-4 1/2" |
| 19396846 | slab | slab > slab | 11'-0 7/8" |
| 19396872 | opening | grid > opening | 3'-1" |
| 19456414 | opening | opening > slab | 12'-11 1/2" |
| 19585158 | slab | wall > slab | 1'-10" |
| 20347836 | slab | column > slab | 7 1/8" |
| 20347856 | slab | column > slab | 10'-11" |
| 20347870 | slab | slab > slab > slab > wall | 10'-3 7/8" | 2'-0" | 10'-2 5/8" |
| 20348075 | slab | column > slab | 12'-11" |
### Extra from the tool (142) - no hand counterpart
| tool dim | cat | references | values |
| 20573949 | slab | slab > grid | 1'-10 1/8" |
| 20573953 | slab | slab > grid | 1'-0 1/2" |
| 20573955 | slab | slab > grid | 1'-2" |
| 20573956 | slab | slab > grid | 3'-2" |
| 20573959 | slab | grid > slab | 6" |
| 20573960 | slab | slab > grid | 4" |
| 20573961 | slab | grid > slab | 4'-1 7/8" |
| 20573962 | slab | slab > grid | 7'-5" |
| 20573963 | slab | grid > slab | 7'-0" |
| 20573965 | slab | slab > slab | 1'-6" |
| 20573969 | slab | slab > slab | 1'-6" |
| 20573970 | slab | slab > slab | 2'-0" |
| 20573971 | slab | slab > slab | 5'-6" |
| 20573972 | slab | slab > slab | 3'-1 1/8" |
| 20573973 | slab | slab > slab | 8" |
| 20573974 | slab | slab > slab | 2'-3" |
| 20573975 | slab | slab > slab | 6 1/8" |
| 20573976 | slab | slab > grid | 2'-6 1/2" |
| 20573977 | slab | slab > grid | 1'-4 7/8" |
| 20573979 | slab | slab > slab | 1'-6" |
| 20573981 | slab | grid > slab | 6" |
| 20573982 | slab | grid > slab | 5 3/4" |
| 20573983 | slab | slab > grid | 1'-0 1/4" |
| 20573985 | slab | slab > grid | 13'-6" |
| 20573986 | slab | slab > slab | 5'-9 1/4" |
| 20573987 | slab | slab > slab | 5'-9 1/4" |
| 20573992 | slab | slab > slab | 11 1/8" |
| 20573997 | slab | slab > grid | 1'-5 1/2" |
| 20573998 | slab | slab > slab | 1'-6" |
| 20573999 | slab | slab > slab | 1'-6" |
| 20574000 | slab | slab > slab | 1'-6" |
| 20574001 | slab | wall > slab | 3'-2" |
| 20574002 | slab | slab > slab | 21'-10" |
| 20574005 | slab | slab > wall | 2'-3" |
| 20574009 | slab | slab > slab | 133'-6" |
| 20574010 | slab | grid > slab | 62'-3" |
| 20574027 | slab | slab > slab | 9'-6 5/8" |
| 20574029 | slab | slab > slab | 9'-6 5/8" |
| 20574033 | slab | slab > slab | 28'-6" |
| 20574034 | beam | beam > grid | 13'-5 1/2" |
| 20574037 | slab | slab > slab | 18'-2" |
| 20574039 | slab | slab > slab | 9'-6 5/8" |
| 20574047 | slab | grid > slab | 12'-8 1/2" |
| 20574053 | slab | slab > slab | 10'-0" |
| 20574054 | slab | grid > slab | 5'-9" |
| 20574055 | slab | slab > slab | 10'-0" |
| 20574056 | slab | slab > grid | 5'-6" |
| 20574059 | slab | slab > slab > slab | 8" | 2'-3" |
| 20574060 | slab | slab > slab > slab > slab | 7'-5 7/8" | 6 1/8" | 6'-7 5/8" |
| 20574061 | slab | wall > slab | 1'-0" |
| 20574062 | beam | beam > beam | 1'-9" |
| 20574063 | slab | slab > slab | 7'-1 3/4" |
| 20574064 | slab | slab > grid | 4'-4 3/8" |
| 20574072 | slab | slab > slab | 3'-3" |
| 20574073 | slab | slab > wall | 3'-10" |
| 20574074 | slab | slab > slab | 1'-5" |
| 20574075 | slab | wall > slab | 5" |
| 20574076 | slab | slab > slab | 3'-6" |
| 20574077 | slab | slab > wall | 4'-4 7/8" |
| 20574078 | slab | slab > slab | 9" |
| 20574081 | slab | slab > slab | 1'-5" |
| 20574083 | slab | slab > slab | 1'-5" |
| 20574084 | slab | grid > slab | 2'-5 1/2" |
| 20574087 | slab | slab > slab | 6" |
| 20574088 | slab | slab > wall | 5'-1 3/4" |
| 20574089 | slab | slab > slab | 2'-0" |
| 20574090 | slab | grid > slab | 1'-0 1/8" |
| 20574091 | slab | slab > slab | 6" |
| 20574092 | slab | slab > wall | 3'-10 3/4" |
| 20574093 | slab | slab > slab | 6" |
| 20574094 | slab | slab > grid | 5'-7 3/8" |
| 20574095 | slab | slab > slab | 1'-2" |
| 20574096 | slab | wall > slab | 2'-7 1/2" |
| 20574097 | slab | slab > slab | 6" |
| 20574098 | slab | slab > grid | 5'-4 1/2" |
| 20574099 | slab | slab > slab | 5" |
| 20574100 | slab | grid > slab | 2 3/8" |
| 20574101 | slab | slab > slab | 6'-8 3/8" |
| 20574103 | slab | slab > slab | 6'-8 3/8" |
| 20574113 | slab | slab > slab | 6'-8 3/8" |
| 20574122 | slab | slab > slab | 1'-6" |
| 20574123 | slab | slab > wall | 2 1/2" |
| 20574124 | slab | grid > slab | 9" |
| 20574125 | slab | slab > slab | 1'-6" |
| 20574126 | slab | grid > slab | 1'-1 1/2" |
| 20574127 | slab | slab > slab | 1'-6" |
| 20574129 | slab | slab > slab | 1'-6" |
| 20574130 | slab | grid > slab | 1'-3 1/2" |
| 20574131 | slab | slab > slab | 1'-6" |
| 20574132 | slab | slab > grid | 7'-10" |
| 20574133 | slab | slab > slab | 1'-6" |
| 20574134 | slab | grid > slab | 1'-1 1/2" |
| 20574135 | slab | slab > slab | 1'-6" |
| 20574136 | slab | slab > grid | 7'-10" |
| 20574137 | slab | slab > slab | 3" |
| 20574138 | slab | slab > grid | 14'-5 1/2" |
| 20574139 | slab | slab > slab | 3" |
| 20574140 | slab | slab > grid | 13'-2 1/2" |
| 20574141 | slab | slab > slab | 10'-8 3/8" |
| 20574151 | slab | slab > slab | 10'-8 3/8" |
| 20574153 | slab | slab > slab | 10'-8 3/8" |
| 20574157 | slab | slab > slab | 1'-6" |
| 20574160 | slab | grid > slab | 2'-9" |
| 20574163 | slab | slab > slab | 1 3/8" |
| 20574164 | slab | slab > wall | 4 1/8" |
| 20574167 | beam | beam > beam | 1'-0" |
| 20574168 | beam | beam > grid | 1'-3 1/2" |
| 20574170 | beam | beam > grid | 13'-0 1/8" |
| 20574174 | beam | beam > column | 8 3/8" |
| 20574175 | beam | beam > beam | 1'-0" |
| 20574176 | beam | grid > beam | 1'-4 1/2" |
| 20574177 | beam | beam > beam | 1'-0" |
| 20574178 | beam | beam > grid > beam | 6" | 6" |
| 20574185 | beam | beam > beam | 5'-6" |
| 20574186 | beam | beam > grid > beam | 2'-9" | 2'-9" |
| 20574187 | beam | grid > beam | 10 7/8" |
| 20574189 | beam | beam > column | 8 3/8" |
| 20574195 | beam | beam > grid | 15'-5" |
| 20574196 | beam | beam > beam | 2'-3" |
| 20574198 | beam | beam > grid | 8'-6 3/8" |
| 20574201 | wall | grid > wall | 1'-3 3/8" |
| 20574202 | wall | wall > grid | 3" |
| 20574203 | wall | wall > grid | 1'-2" |
| 20574204 | wall | wall > grid > wall | 9" | 9" |
| 20574205 | wall | wall > grid | 15'-5 1/4" |
| 20574206 | wall | wall > grid | 1'-3" |
| 20574207 | wall | wall > grid | 11'-0 7/8" |
| 20574208 | wall | grid > wall | 1'-0" |
| 20574211 | wall | grid > wall | 1'-2" |
| 20574213 | wall | wall > grid | 1'-8 1/2" |
| 20574217 | wall | wall > grid | 5'-4" |
| 20574218 | wall | grid > wall | 2" |
| 20574239 | cj | cj > grid | 4'-9" |
| 20574240 | cj | grid > cj | 11'-7 3/4" |
| 20574242 | cj | grid > cj | 1'-2" |
| 20574245 | cj | grid > cj | 4'-4" |
| 20574246 | cj | grid > cj | 8'-4" |
| 20574248 | cj | cj > grid | 9" |
| 20574249 | cj | grid > cj | 7'-7 3/4" |
| 20574250 | cj | cj > grid | 8'-6" |
| 20574251 | cj | cj > grid | 12'-6" |
| 20574252 | cj | grid > cj | 4'-2 1/4" |