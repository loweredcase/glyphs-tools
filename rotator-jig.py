#MenuTitle: Rotator Jig
# -*- coding: utf-8 -*-
__doc__="""
Creates a GUI to automate "rotational" intermediate layers.
"""

# --------------------------------------------------------------------
# Addition Projects - Last Update, Jan 29 2026
# --------------------------------------------------------------------
# Glyph Tools: Rotator Jig
# --------------------------------------------------------------------
# This script uses Vanilla to create a small window where you can:
# → Build Intermediate (brace) layers along an axis for rotation-like interpolation
# → Choose axis, angle range, step degrees, direction, and center point
# → Optionally round node coordinates to integers
# → Safe rerun (rebuilds generated braces)
# → Reset button (undo / ⌘Z)
# --------------------------------------------------------------------


import GlyphsApp
from GlyphsApp import GSLayer
from vanilla import Window, TextBox, EditText, Button, PopUpButton, CheckBox, HorizontalLine
import math


Font = Glyphs.font


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

def brace_name(axisTag, axisValue):
	return f"{{{axisTag}={axisValue}}}"

def copy_shapes_from_to(srcLayer, dstLayer):
	try:
		dstLayer.shapes = []
	except Exception:
		while dstLayer.shapes:
			dstLayer.shapes.pop()
	for sh in srcLayer.shapes:
		dstLayer.shapes.append(sh.copy())
	dstLayer.width = srcLayer.width

def rotate_point(x, y, cx, cy, cosT, sinT):
	dx = x - cx
	dy = y - cy
	rx = cx + (dx * cosT - dy * sinT)
	ry = cy + (dx * sinT + dy * cosT)
	return rx, ry

def rotate_layer_nodes(layer, angleDeg, cx, cy, doRound=False):
	rad = math.radians(angleDeg)
	cosT = math.cos(rad)
	sinT = math.sin(rad)
	for p in layer.paths:
		for n in p.nodes:
			x, y = rotate_point(n.x, n.y, cx, cy, cosT, sinT)
			if doRound:
				n.x = int(round(x))
				n.y = int(round(y))
			else:
				n.x = x
				n.y = y

def axis_items(font):
	tags = []
	tag_to_id = {}
	for ax in (font.axes or []):
		try:
			tag = (ax.axisTag or "").strip()
			if not tag:
				continue
			tags.append(tag)
			tag_to_id[tag] = ax.axisId
		except Exception:
			pass
	return tags, tag_to_id

def set_brace_coordinates(layer, font, master, axisIdToOverride, overrideValue):
	try:
		if layer.attributes is None:
			layer.attributes = {}
	except Exception:
		pass

	try:
		coords = layer.attributes.get("coordinates")
	except Exception:
		coords = None

	if coords is None:
		layer.attributes["coordinates"] = {}
		coords = layer.attributes["coordinates"]

	# Base coordinates = current master axes
	try:
		masterAxes = list(master.axes)
	except Exception:
		masterAxes = []

	for i, ax in enumerate(font.axes or []):
		try:
			baseVal = masterAxes[i] if i < len(masterAxes) else 0
			coords[ax.axisId] = baseVal
		except Exception:
			pass

	# Override chosen axis
	if axisIdToOverride:
		try:
			coords[axisIdToOverride] = int(overrideValue)
		except Exception:
			pass

def remove_existing_braces_for_master(glyph, masterId, axisTag, axisValues):
	names = set(brace_name(axisTag, v) for v in axisValues)
	to_delete = []
	for L in glyph.layers:
		try:
			if getattr(L, "associatedMasterId", None) != masterId:
				continue
			if (L.name or "") in names:
				to_delete.append(L)
		except Exception:
			continue

	for L in reversed(to_delete):
		try:
			glyph.layers.remove(L)
		except Exception:
			try:
				del glyph.layers[glyph.layers.index(L)]
			except Exception:
				pass

def build_degrees_by_step(startDeg, endDeg, stepDeg):
	# Exclude endpoints (masters)
	if stepDeg <= 0:
		return []
	out = []
	d = startDeg + stepDeg
	while d < endDeg - 1e-9:
		out.append(d)
		d += stepDeg
	return out

def map_deg_to_axis_value(deg, startDeg, endDeg, axisMin, axisMaxEffective):
	# Map startDeg..endDeg -> axisMin..axisMaxEffective
	t = (deg - startDeg) / float(endDeg - startDeg)
	return int(round(axisMin + t * (axisMaxEffective - axisMin)))


# ---------- make some interfaces ----------

class RotationJigUI(object):
	def __init__(self):
		self.w = Window((440, 520), "Rotation Jig")

		y = 12

		# CLUSTER 1: Axis & Mapping
		self.w.axisTitle = TextBox((12, y, -12, 16), "AXIS & MAPPING", sizeStyle="small"); y += 18

		self.axisTags, self.axisIdMap = axis_items(Glyphs.font)
		if not self.axisTags:
			self.axisTags = ["(no axes found)"]
			self.axisIdMap = {}

		self.w.axisLabel = TextBox((12, y, 150, 18), "Axis tag:", sizeStyle="small")
		self.w.axisPopup = PopUpButton((160, y, 160, 20), self.axisTags, sizeStyle="small"); y += 26

		self.w.axisMinLabel = TextBox((12, y, 150, 18), "Axis min / max:", sizeStyle="small")
		self.w.axisMin = EditText((160, y, 60, 22), "0", sizeStyle="small")
		self.w.axisMax = EditText((228, y, 60, 22), "1000", sizeStyle="small")
		try:
			self.w.axisMin._nsObject.setPlaceholderString_("min")
			self.w.axisMax._nsObject.setPlaceholderString_("max")
		except Exception:
			pass
		y += 28

		self.w.note999 = TextBox((160, y, -12, 18), "Note: final brace is capped at max-1 (e.g. 999).", sizeStyle="small")
		y += 22

		self.w.sep1 = HorizontalLine((12, y, -12, 1)); y += 10

		# CLUSTER 2: Rotation Frames
		self.w.frameTitle = TextBox((12, y, -12, 16), "ROTATION FRAMES", sizeStyle="small"); y += 18

		self.w.angLabel = TextBox((12, y, 150, 18), "Start / end angle:", sizeStyle="small")
		self.w.angStart = EditText((160, y, 60, 22), "0", sizeStyle="small")
		self.w.angEnd   = EditText((228, y, 60, 22), "90", sizeStyle="small")
		try:
			self.w.angStart._nsObject.setPlaceholderString_("start")
			self.w.angEnd._nsObject.setPlaceholderString_("end")
		except Exception:
			pass
		y += 28

		self.w.stepLabel = TextBox((12, y, 150, 18), "Step degrees:", sizeStyle="small")
		self.w.stepDeg = EditText((160, y, 60, 22), "5", sizeStyle="small")
		self.w.stepHint = TextBox((226, y, -12, 18), "5° → 17 frames (5..85)", sizeStyle="small")
		y += 28

		self.w.dirLabel = TextBox((12, y, 150, 18), "Direction:", sizeStyle="small")
		self.w.dirPopup = PopUpButton((160, y, 200, 20), ["Clockwise", "Counter-clockwise"], sizeStyle="small")
		y += 26

		self.w.centerLabel = TextBox((12, y, 150, 18), "Center X / Y:", sizeStyle="small")
		self.w.centerX = EditText((160, y, 60, 22), "12", sizeStyle="small")
		self.w.centerY = EditText((228, y, 60, 22), "12", sizeStyle="small")
		y += 28

		self.w.roundCheck = CheckBox((12, y, -12, 20), "Round node coordinates to integers", value=False, sizeStyle="small")
		y += 26

		self.w.sep2 = HorizontalLine((12, y, -12, 1)); y += 10

		# Buttons
		self.w.runBtn   = Button((12,  y, 130, 32), "Run 🏁",   callback=self.run)
		self.w.resetBtn = Button((154, y, 130, 32), "Reset ⌘Z", callback=self.reset)
		self.w.closeBtn = Button((296, y, 130, 32), "Close",    callback=self.close)
		y += 44

		# Trim bottom
		x, yy, w, h = self.w.getPosSize()
		self.w.resize(w, y)

		self.w.open()

	def reset(self, sender):
		global Font
		Font = Glyphs.font
		if not Font:
			return
		try:
			doc = Font.parent
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

	def run(self, sender):
		global Font
		Font = Glyphs.font
		if not Font or not Font.selectedLayers:
			print("⚠️ Select at least one glyph layer and run again.")
			return

		currentMaster = Font.selectedFontMaster
		if not currentMaster:
			print("⚠️ No current master found.")
			return
		masterId = currentMaster.id

		axisTag = self.w.axisPopup.getItems()[self.w.axisPopup.get()]
		axisId = self.axisIdMap.get(axisTag, None)
		if not axisId:
			print(f"⚠️ Axis tag '{axisTag}' not found (Font Info → Axes).")
			return

		axisMin = parseInt(self.w.axisMin.get(), 0)
		axisMax = parseInt(self.w.axisMax.get(), 1000)
		if axisMin > axisMax:
			axisMin, axisMax = axisMax, axisMin

		# Critical behavior: cap max to max-1 (e.g. 999)
		axisMaxEffective = axisMax - 1 if axisMax > axisMin else axisMax

		startDeg = parseFloat(self.w.angStart.get(), 0.0)
		endDeg   = parseFloat(self.w.angEnd.get(), 90.0)
		if startDeg > endDeg:
			startDeg, endDeg = endDeg, startDeg

		stepDeg = parseFloat(self.w.stepDeg.get(), 5.0)
		if endDeg - startDeg <= 0:
			print("⚠️ Start/end angle invalid (end must be > start).")
			return

		degrees = build_degrees_by_step(startDeg, endDeg, stepDeg)
		if not degrees:
			print("⚠️ No intermediate frames to build (check step and start/end angles).")
			return

		axisValues = [map_deg_to_axis_value(d, startDeg, endDeg, axisMin, axisMaxEffective) for d in degrees]

		# De-dupe (in case rounding collisions)
		pairs = sorted(set(zip(axisValues, degrees)), key=lambda t: t[0])
		axisValues = [p[0] for p in pairs]
		degrees    = [p[1] for p in pairs]

		cx = parseFloat(self.w.centerX.get(), 0.0)
		cy = parseFloat(self.w.centerY.get(), 0.0)

		clockwise = (self.w.dirPopup.get() == 0)
		roundNodes = bool(self.w.roundCheck.get())

		selectedGlyphs = []
		for L in (Font.selectedLayers or []):
			if L and L.parent and L.parent not in selectedGlyphs:
				selectedGlyphs.append(L.parent)

		if not selectedGlyphs:
			print("⚠️ No glyphs found in selection.")
			return

		dirLabel = "clockwise" if clockwise else "counter-clockwise"
		print(f"↻ Rotation Jig | Master: {currentMaster.name}")
		print(f"↻ Axis: {axisTag} | Range: {axisMin}..{axisMax} (effective max: {axisMaxEffective})")
		print(f"↻ Angles: {startDeg}..{endDeg} | Step: {stepDeg}° | Frames: {len(degrees)} | {dirLabel}")
		print(f"↻ Center: ({cx}, {cy}) | Round nodes: {roundNodes}")

		Font.disableUpdateInterface()
		try:
			for g in selectedGlyphs:
				baseLayer = g.layers[masterId]
				if baseLayer is None:
					continue

				try:
					g.beginUndo()
				except Exception:
					pass

				try:
					remove_existing_braces_for_master(g, masterId, axisTag, axisValues)

					for axisV, deg in zip(axisValues, degrees):
						angleDeg = (-deg) if clockwise else deg

						newLayer = GSLayer()
						newLayer.associatedMasterId = masterId
						newLayer.name = brace_name(axisTag, axisV)

						# Make it a real Intermediate layer (coordinates)
						set_brace_coordinates(newLayer, Font, currentMaster, axisId, axisV)

						g.layers.append(newLayer)

						copy_shapes_from_to(baseLayer, newLayer)
						rotate_layer_nodes(newLayer, angleDeg, cx, cy, doRound=roundNodes)

					print(f"✔ {g.name}: wrote {len(axisValues)} brace layers on {axisTag}.")

				finally:
					try:
						g.endUndo()
					except Exception:
						pass

		finally:
			Font.enableUpdateInterface()
			try:
				Glyphs.redraw()
				if Font.currentTab:
					Font.currentTab.redraw()
			except Exception:
				pass

		print("✅ Done.")

	def close(self, sender):
		self.w.close()


RotationJigUI()
