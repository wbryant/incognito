from xml.etree import ElementTree
import sys


head = '''<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level2" level="2" version="1" xmlns:html="http://www.w3.org/1999/xhtml">
<model id="SIMPLEMERGE" name="model_produced_by_simplemerge.py">
<listOfUnitDefinitions>
	<unitDefinition id="mmol_per_gDW_per_hr">
		<listOfUnits>
			<unit kind="mole" scale="-3"/>
			<unit kind="gram" exponent="-1"/>
			<unit kind="second" multiplier=".00027777" exponent="-1"/>
		</listOfUnits>
	</unitDefinition>
</listOfUnitDefinitions>
<listOfCompartments>
<compartment  id="e"  name="Extracellular"/>
<compartment  id="c"  name="Cytosol"  outside="e"/>
</listOfCompartments>
<listOfSpecies>'''

middle = '''</listOfSpecies>
<listOfReactions>'''

tail = '''</listOfReactions>
</model>
</sbml>
'''

s = dict()
r = dict()

for fname in sys.argv[1:]:
	tree = ElementTree.parse(fname)
	
	specs = tree.findall("{http://www.sbml.org/sbml/level2}model/{http://www.sbml.org/sbml/level2}listOfSpecies/{http://www.sbml.org/sbml/level2}species")
	for x in specs:
		s[x.get("id")] = x
	reacts = tree.findall("{http://www.sbml.org/sbml/level2}model/{http://www.sbml.org/sbml/level2}listOfReactions/{http://www.sbml.org/sbml/level2}reaction")
	for x in reacts:
		specs = x.findall("{http://www.sbml.org/sbml/level2}listOfReactants/{http://www.sbml.org/sbml/level2}speciesReference")
		specs.extend(x.findall("{http://www.sbml.org/sbml/level2}listOfProducts/{http://www.sbml.org/sbml/level2}speciesReference"))
		for y in specs:
			n = y.get("species")
			if n not in s:
				builder = ElementTree.XMLParser()
				builder.feed('<species id="' + n + '" name="unknown" compartment="c" charge="0" boundaryCondition="false"/>')
				e = builder.close()
				s[n] = e
		try:
			notes = x.find("{http://www.sbml.org/sbml/level2}notes")
			x.remove(notes)
		except ValueError:
			pass
		r[x.get("id")] = x




builder = ElementTree.XMLParser()

builder.feed(head)

for x in s.values():
	builder.feed(ElementTree.tostring(x))

builder.feed(middle)

for x in r.values():
	builder.feed(ElementTree.tostring(x))

builder.feed(tail)

sbml = builder.close()


ElementTree.ElementTree(sbml).write("merged.xml")

