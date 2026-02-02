#MenuTitle: Seed Spreader
# -*- coding: utf-8 -*-
__doc__="""
Propagates a parent drawing across all child layers of a glyph.
"""

# --------------------------------------------------------------------
# Addition Projects - Last Update, Feb 2 2026
# --------------------------------------------------------------------
# Glyph Tools: Seed Spreader
# --------------------------------------------------------------------
# This script uses Vanilla to create a small window where you can:
# → Propagate parent drawing to all child layers for selected glyph(s)
# → Optionally copy anchors + width
# → Optionally skip child layers that already contain drawing
# → Run in undo groups + Reset (⌘Z)
# --------------------------------------------------------------------


import GlyphsApp
from GlyphsApp import GSLayer
from vanilla import Window, TextBox, Button, CheckBox, HorizontalLine


Font = Glyphs.font


# ---------------- start your engines ----------------

def layer_has_drawing(layer):
	"""
	Define "contains drawing" conservatively:
	- any shapes (paths/components)
	- OR any anchors
	"""
	try:
		if layer.shapes and len(layer.shapes) > 0:
			return True
	except Exception:
		pass
	try:
		if layer.anchors and len(layer.anchors) > 0:
			return True
	except Exception:
		pass
	return False

def copy_shapes_from_to(srcLayer, dstLayer):
	# Clear destination shapes then copy
	try:
		dstLayer.shapes = []
	except Exception:
		while dstLayer.shapes:
			dstLayer.shapes.pop()

	for sh in srcLayer.shapes:
		dstLayer.shapes.append(sh.copy())

def copy_anchors_from_to(srcLayer, dstLayer):
	# Clear destination anchors then copy
	try:
		dstLayer.anchors = []
	except Exception:
		while dstLayer.anchors:
			dstLayer.anchors.pop()

	for a in srcLayer.anchors:
		try:
			dstLayer.anchors.append(a.copy())
		except Exception:
			# Fallback: some drawings might behave better re-adding copies
			try:
				dstLayer.anchors.append(a.copy())
			except Exception:
				pass

def undo_once():
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
	except Exception as e:
		print(f"⚠️ Reset failed: {e}")
	try:
		if Font.currentTab:
			Font.currentTab.redraw()
		Glyphs.redraw()
	except Exception:
		pass


# ---------------- make an interface ----------------

class SeedSpreaderUI(object):
	def __init__(self):
		self.w = Window((440, 270), "Seed Spreader")

		y = 12

		self.w.title = TextBox(
			(12, y, -12, 18),
			"Copy parent drawing to all child layers",
			sizeStyle="small"
		)
		y += 18

		# Subtitle (italic)
		self.w.subTitle = TextBox((12, y, -12, 18), "Propagate parent drawing to all child layers", sizeStyle="small")
		try:
			self.w.subTitle._nsObject.setFont_(GlyphsApp.NSFont.italicSystemFontOfSize_(11))
		except Exception:
			# If italic font call isn't available in this font, it's fine to stay regular.
			pass
		y += 22

		self.w.sep1 = HorizontalLine((12, y, -12, 1)); y += 12

		self.w.copyShapes = CheckBox((12, y, -12, 20), "Copy shapes (paths + components)", value=True, sizeStyle="small")
		y += 22
		self.w.copyAnchors = CheckBox((12, y, -12, 20), "Copy anchors", value=False, sizeStyle="small")
		y += 22
		self.w.copyWidth = CheckBox((12, y, -12, 20), "Copy width", value=True, sizeStyle="small")
		y += 22

		self.w.skipNonBlank = CheckBox(
			(12, y, -12, 20),
			"Skip child layers that already contain drawing",
			value=False,
			sizeStyle="small"
		)
		y += 26

		self.w.sep2 = HorizontalLine((12, y, -12, 1)); y += 12

		self.w.runBtn   = Button((12,  y, 130, 32), "Run 🏁",   callback=self.run)
		self.w.resetBtn = Button((154, y, 130, 32), "Reset ⌘Z", callback=self.reset)
		self.w.closeBtn = Button((296, y, 130, 32), "Close",    callback=self.close)
		y += 44

		# trim bottom
		x, yy, w, h = self.w.getPosSize()
		self.w.resize(w, y)

		self.w.open()

	def reset(self, sender):
		undo_once()

	def run(self, sender):
		global Font
		Font = Glyphs.font

		if not Font or not Font.selectedLayers:
			print("⚠️ Select one or more glyph layers first.")
			return

		doShapes  = bool(self.w.copyShapes.get())
		doAnchors = bool(self.w.copyAnchors.get())
		doWidth   = bool(self.w.copyWidth.get())
		skipNonBlank = bool(self.w.skipNonBlank.get())

		if not (doShapes or doAnchors or doWidth):
			print("ℹ️ No-op: nothing selected to copy.")
			return

		masters = list(Font.masters or [])
		if len(masters) < 2:
			print("ℹ️ Font has only one master — nothing to propagate.")
			return

		currentMaster = Font.selectedFontMaster
		if not currentMaster:
			print("⚠️ No current master found.")
			return

		# Collect unique glyphs from selection
		selectedGlyphs = []
		for L in (Font.selectedLayers or []):
			if L and L.parent and L.parent not in selectedGlyphs:
				selectedGlyphs.append(L.parent)

		if not selectedGlyphs:
			print("⚠️ No glyphs found in selection.")
			return

		totalTargets = 0
		totalSkipped = 0

		Font.disableUpdateInterface()
		try:
			for g in selectedGlyphs:
				# Parent layer = current master layer for this glyph
				srcLayer = g.layers[currentMaster.id]
				if srcLayer is None:
					continue

				try:
					g.beginUndo()
				except Exception:
					pass

				try:
					for m in masters:
						if m.id == currentMaster.id:
							continue

						dstLayer = g.layers[m.id]
						if dstLayer is None:
							# Ensure a layer exists for that master
							dstLayer = GSLayer()
							dstLayer.associatedMasterId = m.id
							g.layers.append(dstLayer)

						if skipNonBlank and layer_has_drawing(dstLayer):
							totalSkipped += 1
							continue

						if doShapes:
							copy_shapes_from_to(srcLayer, dstLayer)
						if doAnchors:
							copy_anchors_from_to(srcLayer, dstLayer)
						if doWidth:
							try:
								dstLayer.width = srcLayer.width
							except Exception:
								pass

						totalTargets += 1

				finally:
					try:
						g.endUndo()
					except Exception:
						pass

		finally:
			Font.enableUpdateInterface()
			try:
				if Font.currentTab:
					Font.currentTab.redraw()
				Glyphs.redraw()
			except Exception:
				pass

		print(f"✔ Seed Spreader: updated {totalTargets} child layer(s). Skipped {totalSkipped} (already had drawing).")

	def close(self, sender):
		self.w.close()


SeedSpreaderUI()
