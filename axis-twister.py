#MenuTitle: Axis Twister
# -*- coding: utf-8 -*-
__doc__="""
Creates a GUI where you can “twist” Smart Component Axes in a specific glyph or selection of glyphs.
"""

# --------------------------------------------------------------------
# Addition Projects - Last Update, Nov 22 2025
# --------------------------------------------------------------------
# Glyph Tools: Axis Twister
# --------------------------------------------------------------------
# This script uses Vanilla to create a small window where you can:
# → Alter smart component axis values
# → Choose whether to change all axes or only one
# → Choose Random Range or Fixed List per axis
# → In Fixed mode, enter multiple candidate values like “100, 50, 25”
# → Optionally turn some affected components into counters
#    by decomposing and reversing their paths (negative overlaps)
# → Option to make the new glyph on a new layer or in a new glyph
# → Option to rename the layer or new glyph
# → Use a Reset button that calls undo (same as pressing ⌘Z once)
# --------------------------------------------------------------------


import GlyphsApp, random
from GlyphsApp import GSGlyph, GSLayer, GSPath
from vanilla import Window, TextBox, EditText, Button, PopUpButton, CheckBox, HorizontalLine
from datetime import datetime

Font = Glyphs.font
random.seed()  # seed includes OS timestamp for random generator


# ---------- start your engines ----------

def parseInt(s, fallback=0):
	try:
		return int(str(s).strip())
	except Exception:
		return fallback

def parseFloat(s, fallback=0.0):
	try:
		return float(str(s).strip())
	except Exception:
		return fallback

def clamp(v, lo, hi):
	return max(lo, min(hi, v))

def timestamp_str():
	return datetime.now().strftime("%H%M%S")

def parsePool(text):
	return [n.strip() for n in text.replace(";", ",").split(",") if n.strip()]

def discover_axis_names_from_selection(layers):
	names = set()
	for layer in (layers or []):
		for comp in layer.components:
			base = comp.component
			if not base or comp.smartComponentValues is None:
				continue
			axes = base.smartComponentAxes or []
			for ax in axes:
				if ax and ax.name:
					names.add(ax.name)
	return sorted(names)

def axis_map_for_component(comp):
	"""
	Returns: { axisName: (axisID, minVal, maxVal) } for this component.
	"""
	mapping = {}
	base = comp.component
	if not base or comp.smartComponentValues is None:
		return mapping
	axes = base.smartComponentAxes or []
	for ax in axes:
		if not ax:
			continue
		mapping[ax.name] = (
			ax.id,
			float(ax.bottomValue),
			float(ax.topValue),
		)
	return mapping

def findNextVersionedGlyphName(baseName):
	i = 1
	while True:
		candidate = f"{baseName}.{i:03d}"
		if Font.glyphs[candidate] is None:
			return candidate
		i += 1

def duplicateGlyph_withSuffix(glyph, suffix_text=None):
	baseName = glyph.name
	if suffix_text and suffix_text.strip():
		newName = f"{baseName}{suffix_text.strip()}"
		if Font.glyphs[newName] is not None:
			newName = findNextVersionedGlyphName(baseName)
	else:
		newName = findNextVersionedGlyphName(baseName)

	newGlyph = GSGlyph()
	newGlyph.name = newName
	Font.glyphs.append(newGlyph)
	return newGlyph

def masterLayerForId(glyph, masterId):
	try:
		L = glyph.layers[masterId]
		if L is not None:
			return L
	except Exception:
		pass
	L = GSLayer()
	L.associatedMasterId = masterId
	glyph.layers.append(L)
	return L

def copyShapesFromTo(srcLayer, dstLayer):
	try:
		dstLayer.shapes = []
	except Exception:
		while dstLayer.shapes:
			dstLayer.shapes.pop()
	for sh in srcLayer.shapes:
		dstLayer.shapes.append(sh.copy())
	dstLayer.width = srcLayer.width

def duplicateLayer_withName(layer, name_if_any=None, tag="AxisTwist"):
	glyph = layer.parent
	newLayer = layer.copy()
	baseName = layer.name or ""
	label = (name_if_any.strip() if name_if_any and name_if_any.strip()
	         else f"{tag}_{timestamp_str()}")
	newLayer.name = (f"{baseName} {label}".strip() if baseName else label)
	glyph.layers.append(newLayer)
	return newLayer

def focusLayer(layer):
	"""Best-effort focus of a layer in the Edit view."""
	global Font
	try:
		Font.selectedLayers = [layer]
	except Exception:
		pass
	try:
		gName = layer.parent.name
		tab = Font.currentTab
		if tab is None:
			Font.newTab(f"/{gName}")
		else:
			txt = tab.text or ""
			if f"/{gName}" not in txt:
				sep = "" if (not txt or txt.endswith(" ")) else " "
				tab.text = f"{txt}{sep}/{gName}"
		wc = Font.parent.windowController()
		wc.setActiveLayer_(layer)
	except Exception:
		try:
			Font.setCurrentLayer_(layer)
		except Exception:
			pass
	try:
		Glyphs.redraw()
		if Font.currentTab:
			Font.currentTab.redraw()
	except Exception:
		pass


# ---------- make some interfaces ----------

class AxisTwisterUI(object):
	def __init__(self):
		self.w = Window((440, 610), "Axis Twister")

		y = 12

		# CLUSTER 1: Component Scope
		self.w.poolTitle = TextBox((12, y, -12, 16), "COMPONENT SCOPE", sizeStyle="small"); y += 18
		self.w.poolLabel = TextBox((12, y, 150, 18), "Possible components:", sizeStyle="small")
		self.w.pool = EditText(
			(160, y, -12, 22),
			"_part.circle, _part.square, _part.triangle",
			sizeStyle="small"
		)
		y += 28

		self.w.targetLabel = TextBox((12, y, 150, 18), "Target scope:", sizeStyle="small")
		self.w.targetScope = PopUpButton(
			(160, y, 220, 20),
			["All smart components", "Only names in pool"],
			sizeStyle="small"
		)
		y += 26

		self.w.sep1 = HorizontalLine((12, y, -12, 1)); y += 10

		# CLUSTER 2: Axis selection & mode
		self.w.axisTitle = TextBox((12, y, -12, 16), "AXIS SELECTION & MODE", sizeStyle="small"); y += 18

		axis_items = ["All axes"] + discover_axis_names_from_selection(Font.selectedLayers or [])
		self.w.axisLabel = TextBox((12, y, 150, 18), "Axis:", sizeStyle="small")
		self.w.axisPopup = PopUpButton((160, y, 160, 20), axis_items, sizeStyle="small")
		self.w.axisRefresh = Button((326, y-1, 82, 24), "Refresh", callback=self.refreshAxes)
		y += 28

		self.w.modeLabel = TextBox((12, y, 150, 18), "Mode:", sizeStyle="small")
		self.w.modePopup = PopUpButton(
			(160, y, 200, 20),
			["Random range", "Fixed list"],
			sizeStyle="small",
			callback=self.updateEnableStates
		)
		y += 26

		# Random range controls
		self.w.randLabel = TextBox((12, y, 150, 18), "Random range:", sizeStyle="small")
		self.w.randMin = EditText((160, y, 60, 22), "", sizeStyle="small")
		self.w.randMax = EditText((228, y, 60, 22), "", sizeStyle="small")
		try:
			self.w.randMin._nsObject.setPlaceholderString_("min (blank = axis min)")
			self.w.randMax._nsObject.setPlaceholderString_("max (blank = axis max)")
		except Exception:
			pass
		y += 28

		# Fixed list control
		self.w.fixedLabel = TextBox((12, y, 150, 18), "Fixed value list:", sizeStyle="small")
		self.w.fixedValue = EditText((160, y, -12, 22), "", sizeStyle="small")
		try:
			self.w.fixedValue._nsObject.setPlaceholderString_("e.g. 100, 50, 25")
		except Exception:
			pass
		y += 28

		self.w.pctLabel = TextBox((12, y, 150, 18), "Chance % (0–100):", sizeStyle="small")
		self.w.pct = EditText((160, y, 60, 22), "100", sizeStyle="small")
		y += 28

		self.w.modLabel = TextBox((12, y, 180, 18), "Affected components:", sizeStyle="small")
		self.w.modulo = EditText((160, y, 60, 22), "1", sizeStyle="small")
		self.w.modHint = TextBox(
			(230, y, -12, 18),
			"1 = all, 2 = every other, 3 = every third ...",
			sizeStyle="mini" 
		)
		y += 24

		self.w.randomCounter = CheckBox(
			(12, y, -12, 20),
			"Random counters: decompose & reverse some affected components.",
			value=False,
			sizeStyle="small",
			callback=self.updateEnableStates
		)
		y += 22

		self.w.counterChanceLabel = TextBox((32, y, 130, 18), "Counter chance %:", sizeStyle="small")
		self.w.counterChance = EditText((162, y, 60, 22), "50", sizeStyle="small")
		try:
			self.w.counterChance._nsObject.setPlaceholderString_("0–100")
		except Exception:
			pass
		y += 30

		self.w.sep2 = HorizontalLine((12, y, -12, 1)); y += 10

		# CLUSTER 3: Save options
		self.w.saveTitle = TextBox((12, y, -12, 16), "SAVE OPTIONS", sizeStyle="small"); y += 18

		self.w.makeNewLayer = CheckBox(
			(12, y, -12, 20),
			"Create new layer (non-destructive).",
			value=False,
			sizeStyle="small",
			callback=self.updateEnableStates
		)
		y += 22

		self.w.layerNameLabel = TextBox((12, y, -12, 16), "New layer name (optional):", sizeStyle="small")
		y += 18

		self.w.layerName = EditText((12, y, -12, 22), "", sizeStyle="small")
		try:
			self.w.layerName._nsObject.setPlaceholderString_("e.g. AxisTwist_123045")
		except Exception:
			pass
		y += 26

		self.w.openTab = CheckBox(
			(24, y, -12, 20),
			"Open new layer in a new Edit tab.",
			value=False,
			sizeStyle="small"
		)
		y += 30

		self.w.makeNewGlyph = CheckBox(
			(12, y, -12, 20),
			"Draw to a new glyph (duplicate the glyph first).",
			value=False,
			sizeStyle="small",
			callback=self.updateEnableStates
		)
		y += 22

		self.w.glyphSuffixLabel = TextBox((12, y, -12, 16), "New glyph suffix (optional):", sizeStyle="small")
		y += 18

		self.w.glyphSuffix = EditText((12, y, -12, 22), "", sizeStyle="small")
		try:
			self.w.glyphSuffix._nsObject.setPlaceholderString_(".alt  or  .ss01   (blank = auto .001)")
		except Exception:
			pass
		y += 32

		self.w.sep3 = HorizontalLine((12, y, -12, 1)); y += 10

		# Buttons
		self.w.runBtn   = Button((12,  y, 130, 32), "Run 🏁",   callback=self.run)
		self.w.resetBtn = Button((154, y, 130, 32), "Reset ⌘Z", callback=self.reset)
		self.w.closeBtn = Button((296, y, 130, 32), "Close",    callback=self.close)
		y += 44

		# Trim bottom
		x, yy, w, h = self.w.getPosSize()
		self.w.resize(w, y)

		self.updateEnableStates()
		self.w.open()

	# ---------- edit view updates ----------

	def refreshAxes(self, sender):
		items = ["All axes"] + discover_axis_names_from_selection(Font.selectedLayers or [])
		self.w.axisPopup.setItems(items)

	def updateEnableStates(self, sender=None):
		modeIdx = self.w.modePopup.get()  # 0=Random range, 1=Fixed list

		# Random range vs Fixed list fields
		self.w.randLabel.enable(modeIdx == 0)
		self.w.randMin.enable(modeIdx == 0)
		self.w.randMax.enable(modeIdx == 0)

		self.w.fixedLabel.enable(modeIdx == 1)
		self.w.fixedValue.enable(modeIdx == 1)

		# New layer / tab logic
		makeNewLayer = bool(self.w.makeNewLayer.get())
		makeNewGlyph = bool(self.w.makeNewGlyph.get())

		allowLayerControls = makeNewLayer and not makeNewGlyph
		self.w.layerName.enable(allowLayerControls)
		self.w.openTab.enable(allowLayerControls)

		# Counter chance only when random counters is ON
		rc = bool(self.w.randomCounter.get())
		self.w.counterChanceLabel.enable(rc)
		self.w.counterChance.enable(rc)

	# ---------- oh shit undo ----------

	def reset(self, sender):
		"""
		Reset button: calls the document's undo manager once,
		which should undo the last script operation (same as ⌘Z).
		"""
		global Font
		Font = Glyphs.font
		if not Font:
			return
		try:
			doc = Font.parent  # GSDocument
			if doc and hasattr(doc, "undoManager"):
				um = doc.undoManager()
				if um:
					um.undo()
			else:
				# Fallback: glyph-level undo for selected layers
				for layer in (Font.selectedLayers or []):
					g = layer.parent
					if hasattr(g, "undoManager"):
						um = g.undoManager()
						if um:
							um.undo()
		except Exception as e:
			print(f"⚠️ Reset failed: {e}")
		# Redraw after undo
		try:
			if Font.currentTab:
				Font.currentTab.redraw()
			Glyphs.redraw()
		except Exception:
			pass

	# ---------- axis helpers ----------

	def axis_targets_for_component(self, comp):
		axisIdx = self.w.axisPopup.get()
		items = self.w.axisPopup.getItems()
		if not items:
			return []

		selected_name = items[axisIdx]
		amap = axis_map_for_component(comp)
		out = []
		if not amap:
			return out

		if selected_name == "All axes":
			for nm, (axid, lo, hi) in amap.items():
				out.append((nm, axid, lo, hi))
		else:
			if selected_name in amap:
				axid, lo, hi = amap[selected_name]
				out.append((selected_name, axid, lo, hi))

		return out

	# ---------- the main event ----------

	def run(self, sender):
		global Font
		Font = Glyphs.font

		if not Font or not Font.selectedLayers:
			print("⚠️ Select one or more glyph layers first.")
			return

		pool = parsePool(self.w.pool.get())
		scopeIdx = self.w.targetScope.get()  # 0 = All smart components, 1 = Only names in pool

		modeIdx = self.w.modePopup.get()     # 0 = Random range, 1 = Fixed list
		chance = clamp(parseInt(self.w.pct.get(), 100), 0, 100)
		moduloN = max(1, parseInt(self.w.modulo.get(), 1))
		randomCounters = bool(self.w.randomCounter.get())
		counterChance = clamp(parseInt(self.w.counterChance.get(), 50), 0, 100)

		# range parameters
		randMinText = self.w.randMin.get()
		randMaxText = self.w.randMax.get()
		fixedText   = self.w.fixedValue.get()

		# parse fixed list into floats
		fixedCandidates = []
		if fixedText.strip():
			for tok in parsePool(fixedText):
				try:
					val = float(tok)
					fixedCandidates.append(val)
				except Exception:
					pass

		if modeIdx == 1 and not fixedCandidates:
			print("⚠️ Fixed list mode is active, but the list is empty or invalid.")
			return

		makeNewLayer = bool(self.w.makeNewLayer.get())
		layerName = self.w.layerName.get().strip() if makeNewLayer else ""
		openTab = bool(self.w.openTab.get())

		makeNewGlyph = bool(self.w.makeNewGlyph.get())
		glyphSuffix = self.w.glyphSuffix.get().strip() if makeNewGlyph else ""

		# collect selected layers grouped by source glyph
		byGlyph = {}
		for srcLayer in Font.selectedLayers:
			byGlyph.setdefault(srcLayer.parent, []).append(srcLayer)

		if not byGlyph:
			print("⚠️ No valid layers found.")
			return

		random.seed()

		twistedAxesCount = 0
		touchedComponents = 0

		layersToFocus = []
		lastLayerToFocus = None

		Font.disableUpdateInterface()
		glyphsToUndo = set()
		try:
			# decide target glyphs
			glyphMap = {}
			for srcGlyph, srcLayers in byGlyph.items():
				if makeNewGlyph:
					tgtGlyph = duplicateGlyph_withSuffix(srcGlyph, glyphSuffix)
				else:
					tgtGlyph = srcGlyph
				glyphMap[srcGlyph] = tgtGlyph
				glyphsToUndo.add(tgtGlyph)

			# begin undo groups
			for g in glyphsToUndo:
				try:
					g.beginUndo()
				except Exception:
					pass

			try:
				# build target layers
				layersToProcess = []
				for srcGlyph, srcLayers in byGlyph.items():
					tgtGlyph = glyphMap[srcGlyph]
					for srcLayer in srcLayers:
						masterId = getattr(srcLayer, "associatedMasterId", None)
						if not masterId:
							continue

						if makeNewGlyph:
							targetLayer = masterLayerForId(tgtGlyph, masterId)
							copyShapesFromTo(srcLayer, targetLayer)
							workingLayer = targetLayer
							lastLayerToFocus = workingLayer
						else:
							if makeNewLayer:
								workingLayer = duplicateLayer_withName(
									srcLayer,
									name_if_any=layerName,
									tag="AxisTwist"
								)
								layersToFocus.append(workingLayer)
							else:
								workingLayer = srcLayer

						layersToProcess.append(workingLayer)

				# apply axis twisting
				for layer in layersToProcess:
					compIndex = 0
					# iterate over a copy because we may decompose components
					for comp in list(layer.components):
						vals = comp.smartComponentValues
						if vals is None:
							continue

						# scope: only certain components if requested
						if scopeIdx == 1:
							if not comp.componentName or comp.componentName not in pool:
								continue

						compIndex += 1

						# modulo opperation: only every Nth smart component
						if moduloN > 1 and (compIndex % moduloN) != 0:
							continue

						# chance per component
						if random.random() > (chance / 100.0):
							continue

						targetAxes = self.axis_targets_for_component(comp)
						if not targetAxes:
							continue

						for axisName, axisID, lo, hi in targetAxes:
							loAxis = float(lo)
							hiAxis = float(hi)
							if loAxis > hiAxis:
								loAxis, hiAxis = hiAxis, loAxis

							if modeIdx == 0:
								# random range
								if randMinText.strip() or randMaxText.strip():
									rMin = parseFloat(randMinText, loAxis)
									rMax = parseFloat(randMaxText, hiAxis)
								else:
									rMin = loAxis
									rMax = hiAxis
								if rMin > rMax:
									rMin, rMax = rMax, rMin
								raw = random.uniform(rMin, rMax)
							else:
								# fixed list: pick randomly from candidates
								raw = random.choice(fixedCandidates)

							newVal = clamp(raw, loAxis, hiAxis)
							vals[axisID] = newVal
							twistedAxesCount += 1

						touchedComponents += 1

						# random counters: decompose this component and reverse new paths
						if randomCounters and random.random() <= (counterChance / 100.0):
							try:
								beforeShapes = list(layer.shapes)
								old_ids = set(id(s) for s in beforeShapes)
								comp.decompose()
								newShapes = [s for s in layer.shapes if id(s) not in old_ids]
								for sh in newShapes:
									if isinstance(sh, GSPath):
										try:
											sh.reverse()
										except Exception:
											pass
							except Exception as e:
								print(f"⚠️ Counter conversion failed for {comp.componentName}: {e}")

			finally:
				# end undo groups
				for g in glyphsToUndo:
					try:
						g.endUndo()
					except Exception:
						pass

		finally:
			Font.enableUpdateInterface()

		# --- focus & tab updates for new glyphs ---

		if makeNewGlyph:
			tab = Font.currentTab
			if tab is None:
				# no tab yet: show all target glyphs
				tabText = " ".join(f"/{glyphMap[src].name}" for src in byGlyph.keys())
				Font.newTab(tabText)
			else:
				txt = tab.text or ""
				if txt.strip():
					tokens = txt.split()
				else:
					tokens = []

				# insert each new glyph token right after its source glyph token
				for srcGlyph, tgtGlyph in glyphMap.items():
					if srcGlyph == tgtGlyph:
						continue
					srcToken = f"/{srcGlyph.name}"
					tgtToken = f"/{tgtGlyph.name}"
					if tgtToken in tokens:
						continue

					inserted = False
					i = 0
					while i < len(tokens):
						if tokens[i] == srcToken:
							tokens.insert(i + 1, tgtToken)
							inserted = True
							i += 2
						else:
							i += 1

					if not inserted:
						tokens.append(tgtToken)

				tab.text = " ".join(tokens)

			if lastLayerToFocus is not None:
				focusLayer(lastLayerToFocus)

		elif layersToFocus:
			# no new glyph, but we may have new layers
			if openTab:
				Font.newTab([layersToFocus[-1]])
			else:
				focusLayer(layersToFocus[-1])

		# final redraw
		try:
			if Font.currentTab:
				Font.currentTab.redraw()
			Glyphs.redraw()
		except Exception:
			pass

		modeMsg = "Random range" if modeIdx == 0 else "Fixed list"
		scopeMsg = "All smart components" if scopeIdx == 0 else "Only names in pool"
		layerMsg = f"NewLayer={'YES' if (makeNewLayer and not makeNewGlyph) else 'NO'}"
		glyphMsg = f"NewGlyph={'YES' if makeNewGlyph else 'NO'}"
		counterMsg = "RandomCounters=ON" if randomCounters else "RandomCounters=OFF"

		print(
			f"✔ Axis Twister: set {twistedAxesCount} axis value(s) on {touchedComponents} component(s). "
			f"Mode={modeMsg}, Scope={scopeMsg}, Chance={chance}%, Modulo={moduloN}, "
			f"{layerMsg}, {glyphMsg}, {counterMsg}, CounterChance={counterChance}%."
		)

	def close(self, sender):
		self.w.close()


AxisTwisterUI()
