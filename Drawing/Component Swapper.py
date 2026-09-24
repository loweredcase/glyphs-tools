#MenuTitle: Component Swapper
# -*- coding: utf-8 -*-
__doc__="""
Creates a GUI where you can control swapping components in a specific glyph or selection of glyphs.
"""

# --------------------------------------------------------------------
# Addition Projects - Last Update, Sep 24 2026
# --------------------------------------------------------------------
# Glyph Tools: Component Swapper
# --------------------------------------------------------------------
# This script uses Vanilla to create a small window where you can:
# → Choose or type the target component to replace
# → Enter a comma-separated list of replacement components
# → Replace randomly from that list, or cycle A → B → C → A → …
# → Optionally target all components instead of one named component
# → Optionally alternate every other component
# → Option to make the new glyph on a new layer or in a new glyph
# → Option to rename the layer or new glyph
# → Use a Reset button that calls undo (same as pressing ⌘Z once)
# --------------------------------------------------------------------


import GlyphsApp, random
from GlyphsApp import GSGlyph, GSLayer
from vanilla import FloatingWindow, TextBox, EditText, Button, PopUpButton, CheckBox, ComboBox, HorizontalLine
from datetime import datetime

Font = Glyphs.font
random.seed()  # seed includes OS timestamp for random generator


# ---------- start your engines ----------

def parsePool(text):
	return [n.strip() for n in text.replace(";", ",").split(",") if n.strip()]

def gate(percent_str):
	try:
		p = int(percent_str)
	except Exception:
		p = 100
	p = max(0, min(100, p))
	return random.random() <= (p / 100.0)

def setComponentName(comp, newName):
	try:
		comp.componentName = newName
	except Exception:
		try:
			g = Font.glyphs[newName]
		except Exception:
			g = None
		if g:
			comp.component = g

def timestamp_str():
	return datetime.now().strftime("%H%M%S")

def duplicateLayer_withName(layer, name_if_any=None, tag="SwapComponents"):
	glyph = layer.parent
	newLayer = layer.copy()
	baseName = layer.name or ""
	label = (name_if_any.strip() if name_if_any and name_if_any.strip()
			 else f"{tag}_{timestamp_str()}")
	newLayer.name = (f"{baseName} {label}".strip() if baseName else label)
	glyph.layers.append(newLayer)
	return newLayer

def uniqueComponentNamesInSelection():
	names = set()
	for layer in (Font.selectedLayers or []):
		for comp in layer.components:
			n = (comp.componentName or "").strip()
			if n:
				names.add(n)
	return sorted(names)

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

def focusLayer(layer):
	"""Best-effort focus of a layer in the Edit view."""
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

class SwapComponentsGUI(object):
	def __init__(self):
		self.w = FloatingWindow((440, 610), "Component Swapper")
		self.lastUndoGlyphs = []
		self.lastCreatedGlyphNames = []

		y = 12
		# CLUSTER 1: Target + replacements
		self.w.targetLabel = TextBox((12, y, 160, 18), "Target component:", sizeStyle="small")
		self.w.targetName = ComboBox((172, y, -12, 22), [], sizeStyle="small")
		try:
			self.w.targetName.getNSComboBox().setPlaceholderString_("type or choose, e.g. pixel")
		except Exception:
			pass
		y += 28

		self.w.scopeLabel = TextBox((12, y, 160, 18), "Target scope:", sizeStyle="small")
		self.w.scope = PopUpButton((172, y, -12, 20), ["Only target above", "All components"], sizeStyle="small", callback=self.updateEnableStates); y += 26

		self.w.poolTitle = TextBox((12, y, 160, 18), "Replacement components:", sizeStyle="small")
		self.w.pool = EditText((172, y, -12, 22), "_part.circle, _part.square, _part.triangle", sizeStyle="small"); y += 28
		try:
			self.w.pool._nsObject.setPlaceholderString_("comma-separated glyph names")
		except Exception:
			pass

		self.w.replModeLabel = TextBox((12, y, 160, 18), "Replacement order:", sizeStyle="small")
		self.w.replMode = PopUpButton((172, y, -12, 20), ["Random", "Cycle through list"], sizeStyle="small", callback=self.updateEnableStates); y += 26

		self.w.pctLabel = TextBox((12, y, 160, 18), "Swap chance (%):", sizeStyle="small")
		self.w.pct = EditText((172, y, 60, 22), "100", sizeStyle="small"); y += 28

		self.w.modCheck = CheckBox((12, y, 220, 20), "Alternate every other", value=False, sizeStyle="small", callback=self.updateEnableStates)
		self.w.modStartLabel = TextBox((240, y, 40, 18), "Start:", sizeStyle="small")
		self.w.modStart = PopUpButton((284, y, -12, 20), ["Even (0,2,4…)", "Odd (1,3,5…)"], sizeStyle="small"); y += 30

		self.w.sep2 = HorizontalLine((12, y, -12, 1)); y += 14

		# CLUSTER 3: Save options — New Layer (in-place)
		self.w.makeNewLayer = CheckBox((12, y, -12, 20), "Create new layer before running (non-destructive).", value=False, sizeStyle="small", callback=self.updateEnableStates); y += 22
		self.w.layerNameLabel = TextBox((12, y, -12, 16), "New layer name (optional):", sizeStyle="small"); y += 18
		self.w.layerName = EditText((12, y, -12, 22), "", sizeStyle="small")
		try:
			self.w.layerName._nsObject.setPlaceholderString_("e.g. SwapComponents_123045")
		except Exception:
			pass
		y += 26

		# Open-tab option is clustered with New Layer
		self.w.openTab = CheckBox((24, y, -12, 20), "Open new layer in a new Edit tab (guaranteed focus).", value=False, sizeStyle="small"); y += 30

		self.w.sep3 = HorizontalLine((12, y, -12, 1)); y += 14

		# CLUSTER 4: Save options — New Glyph
		self.w.makeNewGlyph = CheckBox((12, y, -12, 20), "Draw to a new glyph (duplicate the glyph first).", value=False, sizeStyle="small", callback=self.updateEnableStates); y += 22
		self.w.glyphSuffixLabel = TextBox((12, y, -12, 16), "New glyph suffix (optional):", sizeStyle="small"); y += 18
		self.w.glyphSuffix = EditText((12, y, -12, 22), "", sizeStyle="small")
		try:
			self.w.glyphSuffix._nsObject.setPlaceholderString_(".alt  or  .expA   (blank = auto .001)")
		except Exception:
			pass
		y += 32

		# Buttons (Run / Reset / Close)
		self.w.runBtn   = Button((12,  y, 130, 32), "Run 🏁",   callback=self.run)
		self.w.resetBtn = Button((154, y, 130, 32), "Reset ⌘Z", callback=self.reset)
		self.w.closeBtn = Button((296, y, 130, 32), "Close",    callback=self.closeWindow)
		y += 44

		# Trim bottom
		x, yy, w, h = self.w.getPosSize()
		self.w.resize(w, y)

		random.seed()
		self.refreshFromSelection(preserve=False)
		self.updateEnableStates()
		self.w.open()

	# ---------- edit view updates ----------

	def refreshFromSelection(self, preserve=True):
		# ComboBox is editable: keep whatever the user typed, while refreshing suggestions.
		old_text = ""
		if preserve:
			try:
				old_text = (self.w.targetName.get() or "").strip()
			except Exception:
				pass
		names = uniqueComponentNamesInSelection()
		self.w.targetName.setItems(names)
		if old_text:
			self.w.targetName.set(old_text)
		elif names:
			self.w.targetName.set(names[0])
		else:
			self.w.targetName.set("")

	def onPoolChange(self, sender):
		self.updateEnableStates()

	def updateEnableStates(self, sender=None):
		# Target field is only needed in specific-target mode.
		self.w.targetName.enable(self.w.scope.get() == 0)
		self.w.modStart.enable(bool(self.w.modCheck.get()))
		# openTab only if New Layer is on and NOT New Glyph
		self.w.openTab.enable(bool(self.w.makeNewLayer.get()) and not bool(self.w.makeNewGlyph.get()))
		# If making a New Glyph, layer naming/open-tab doesn’t apply
		self.w.layerName.enable(bool(self.w.makeNewLayer.get()) and not bool(self.w.makeNewGlyph.get()))

	# ---------- oh shit undo ----------

	def reset(self, sender):
		"""Undo the last Component Swapper operation in Glyphs 4."""
		global Font
		Font = Glyphs.font
		if not Font:
			return

		try:
			if self.lastCreatedGlyphNames:
				for glyphName in list(self.lastCreatedGlyphNames):
					glyph = Font.glyphs[glyphName]
					if glyph is not None:
						Font.glyphs.remove(glyph)
				self.lastCreatedGlyphNames = []
			else:
				undoGlyphs = self.lastUndoGlyphs or [layer.parent for layer in (Font.selectedLayers or [])]
				seen = set()
				for glyph in undoGlyphs:
					if glyph is None or id(glyph) in seen:
						continue
					seen.add(id(glyph))
					try:
						um = glyph.undoManager()
						if um and um.canUndo():
							um.undo()
					except Exception as e:
						print(f"⚠️ Could not undo {glyph.name}: {e}")
		except Exception as e:
			print(f"⚠️ Reset failed: {e}")

		try:
			if Font.currentTab:
				Font.currentTab.redraw()
			Glyphs.redraw()
		except Exception:
			pass

	# ---------- the main event ----------

	def run(self, sender):
		global Font
		Font = Glyphs.font  # refresh in case user switched fonts

		if not Font or not Font.selectedLayers:
			print("⚠️ Select one or more glyph layers first.")
			return

		self.refreshFromSelection(preserve=True)

		replacementList = parsePool(self.w.pool.get())
		scopeIdx = self.w.scope.get()                      # 0=Only target, 1=All components
		scopeName = (self.w.targetName.get() or "").strip()
		replModeIdx = self.w.replMode.get()                # 0=Random, 1=Cycle

		if not replacementList:
			print("⚠️ Add at least one replacement component.")
			return
		if scopeIdx == 0 and not scopeName:
			print("⚠️ Choose or type a target component name.")
			return

		swapPct       = self.w.pct.get()
		useModulo     = bool(self.w.modCheck.get())
		startOdd      = (self.w.modStart.get() == 1)

		makeNewLayer  = bool(self.w.makeNewLayer.get())
		newLayerName  = self.w.layerName.get().strip() if makeNewLayer else ""

		makeNewGlyph  = bool(self.w.makeNewGlyph.get())
		glyphSuffix   = self.w.glyphSuffix.get().strip() if makeNewGlyph else ""
		openNewTab    = bool(self.w.openTab.get())

		swappedCount = 0
		processedLayers = 0

		layersToFocus = []      # for new layers (same glyph)
		lastLayerToFocus = None # for focusing a layer in duplicated glyph

		Font.disableUpdateInterface()
		glyphsToUndo = set()
		try:
			# group selected layers by parent glyph
			byGlyph = {}
			for srcLayer in Font.selectedLayers:
				byGlyph.setdefault(srcLayer.parent, []).append(srcLayer)

			# decide target glyph per source glyph (dup if requested)
			glyphMap = {}
			for srcGlyph, layers in byGlyph.items():
				tgtGlyph = duplicateGlyph_withSuffix(srcGlyph, glyphSuffix) if makeNewGlyph else srcGlyph
				glyphMap[srcGlyph] = tgtGlyph
				glyphsToUndo.add(tgtGlyph)

			# begin undo groups for all target glyphs
			for g in glyphsToUndo:
				try:
					g.beginUndo()
				except Exception:
					pass

			try:
				# build exact target layers and ensure correct content location
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
									name_if_any=newLayerName,
									tag="SwapComponents"
								)
								layersToFocus.append(workingLayer)
							else:
								workingLayer = srcLayer

						layersToProcess.append(workingLayer)

				# apply swaps
				specIndex = 0  # counts how many specific replacements we've done
				for layer in layersToProcess:
					processedLayers += 1
					for idx, comp in enumerate(layer.components):
						compName = (comp.componentName or "").strip()
						if not compName:
							continue

						# ---- TARGETING ----
						if scopeIdx == 0 and compName != scopeName:
							continue

						# Modulo behavior:
						# - Random mode: modulo decides WHETHER we swap (skip some)
						# - Specific list mode: modulo decides WHICH item in the list we use (pattern),
						#   but we still swap every targeted component.
						if replModeIdx == 0 and useModulo:
							# RANDOM MODE: only swap every other targeted component
							if startOdd and (idx % 2 == 0):
								continue
							if (not startOdd) and (idx % 2 == 1):
								continue

						# Chance
						if not gate(swapPct):
							continue

						# ---- REPLACEMENT ----
						if replModeIdx == 0:
							newName = random.choice(replacementList)
						else:
							offset = 1 if (useModulo and startOdd) else 0
							repIndex = (specIndex + offset) % len(replacementList)
							newName = replacementList[repIndex]
							specIndex += 1

						try:
							comp.automaticAlignment = False  # keep position stable
						except Exception:
							pass
						setComponentName(comp, newName)
						swappedCount += 1

			finally:
				# end undo groups for all target glyphs
				for g in glyphsToUndo:
					try:
						g.endUndo()
					except Exception:
						pass

		finally:
			Font.enableUpdateInterface()

		# Remember the last operation for the Reset button.
		self.lastUndoGlyphs = list(glyphsToUndo)
		self.lastCreatedGlyphNames = [g.name for g in glyphsToUndo] if makeNewGlyph else []

		# --- focus & tab updates ---

		if makeNewGlyph:
			tab = Font.currentTab
			if tab is None:
				# No tab yet: show all *target* glyphs
				tabText = " ".join(f"/{glyphMap[src].name}" for src in byGlyph.keys())
				Font.newTab(tabText)
			else:
				txt = tab.text or ""
				if txt.strip():
					tokens = txt.split()
				else:
					tokens = []

				# For each source glyph, insert its new glyph token right after it
				for srcGlyph, tgtGlyph in glyphMap.items():
					if srcGlyph == tgtGlyph:
						continue  # not a duplicated glyph
					srcToken = f"/{srcGlyph.name}"
					tgtToken = f"/{tgtGlyph.name}"
					if tgtToken in tokens:
						continue  # already present

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
						# if we never saw the source token, append at the end
						tokens.append(tgtToken)

				tab.text = " ".join(tokens)

			if lastLayerToFocus is not None:
				focusLayer(lastLayerToFocus)

		elif layersToFocus:
			# no new glyph, but we may have new layers
			if openNewTab:
				Font.newTab([layersToFocus[-1]])  # guaranteed focus
			else:
				focusLayer(layersToFocus[-1])

		# final redraw
		try:
			if Font.currentTab:
				Font.currentTab.redraw()
			Glyphs.redraw()
		except Exception:
			pass

		scopeMsg = f"Only '{scopeName}'" if scopeIdx == 0 else "All components"
		if replModeIdx == 0:
			replMsg = f"Random ({len(replacementList)} item(s))"
		else:
			replMsg = f"Cycle ({len(replacementList)} item(s))"
		modMsg   = "Modulo ON" if useModulo else "Modulo OFF"
		layerMsg = f"NewLayer={'YES' if (makeNewLayer and not makeNewGlyph) else 'NO'}"
		glyphMsg = f"NewGlyph={'YES' if makeNewGlyph else 'NO'}"
		print(
			f"✔ Swapped {swappedCount} component(s) across {processedLayers} layer(s). "
			f"Scope={scopeMsg}, Replacement={replMsg}, Chance={swapPct}%, {modMsg}, {layerMsg}, {glyphMsg}."
		)


	def closeWindow(self, sender):
		try:
			self.w.getNSWindow().performClose_(sender)
		except Exception:
			self.w.close()


SwapComponentsGUI()
