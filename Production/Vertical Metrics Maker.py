#MenuTitle: Vertical Metrics Maker
# -*- coding: utf-8 -*-
__doc__ = """
Adds and sets recommended vertical-metric custom parameters in Glyphs 4.
"""


# --------------------------------------------------------------------
# Addition Projects - Last Update, Oct 4 2026
# --------------------------------------------------------------------
# Glyph Tools: Vertical Metrics Maker
# --------------------------------------------------------------------
# This script uses Vanilla to create a small window where you can:
# → Metric recipe dropdown (Recommended default)
# → Preview pane (compute first, then write)
# → Font-level OpenType vertical metrics
# → Removal of conflicting Master-level metric overrides
# → Robust create-or-update writing (safe to rerun)
# → Reset button (one undo step / ⌘Z)
# --------------------------------------------------------------------


import math
import GlyphsApp
from AppKit import NSColor
from vanilla import (
	Window,
	TextBox,
	EditText,
	Button,
	PopUpButton,
	CheckBox,
	HorizontalLine,
	TextEditor,
)

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


def ceil_int(v):
	try:
		return int(math.ceil(float(v)))
	except Exception:
		return int(v)


def round_int(v):
	try:
		return int(round(float(v)))
	except Exception:
		return int(v)


def set_param(container, key, value):
	"""
	Robust create-or-update writer for GSFont / GSFontMaster.
	Overwrites existing values cleanly.
	"""
	try:
		container.setCustomParameter_forKey_(value, key)
		return True
	except Exception:
		pass

	try:
		container.customParameters[key] = value
		return True
	except Exception:
		return False


def remove_param(container, key):
	"""
	Remove a custom parameter if present.
	Used to clear Master-level overrides before writing Font-level metrics.
	"""
	try:
		del container.customParameters[key]
		return True
	except Exception:
		pass

	try:
		container.removeObjectFromCustomParametersForKey_(key)
		return True
	except Exception:
		return False


def get_layer_bounds(layer):
	"""
	Return (minY, maxY) for a layer.
	Prefer complete bounds (includes components) when available.
	"""
	if layer is None:
		return None

	for attr in (
		"completeBounds",
		"completeBoundsIncludingTransforms",
		"boundsIncludingComponents",
	):
		try:
			obj = getattr(layer, attr, None)
			if obj is None:
				continue

			b = obj() if callable(obj) else obj

			if b and b.size and b.size.height:
				h = float(b.size.height)

				if h <= 0:
					continue

				minY = float(b.origin.y)
				maxY = float(b.origin.y + b.size.height)

				return (minY, maxY)

		except Exception:
			pass

	try:
		b = layer.bounds

		if b and b.size and b.size.height:
			h = float(b.size.height)

			if h > 0:
				minY = float(b.origin.y)
				maxY = float(b.origin.y + b.size.height)

				return (minY, maxY)

	except Exception:
		pass

	try:
		b = layer.fastBounds

		if b and b.size and b.size.height:
			h = float(b.size.height)

			if h > 0:
				minY = float(b.origin.y)
				maxY = float(b.origin.y + b.size.height)

				return (minY, maxY)

	except Exception:
		pass

	return None


def exportable_glyphs(font):
	out = []

	for g in (font.glyphs or []):
		try:
			if g and g.export:
				out.append(g)
		except Exception:
			continue

	return out


def selected_glyphs(font):
	out = []

	for L in (font.selectedLayers or []):
		try:
			if L and L.parent and L.parent not in out:
				out.append(L.parent)
		except Exception:
			continue

	return out


def master_list(font):
	return list(font.masters or [])


def doc_undo_once(font):
	try:
		doc = font.parent

		if doc and hasattr(doc, "undoManager"):
			um = doc.undoManager()

			if um:
				um.undo()

	except Exception:
		pass


def begin_doc_undo_group(font):
	try:
		doc = font.parent

		if doc and hasattr(doc, "undoManager"):
			um = doc.undoManager()

			if um and hasattr(um, "beginUndoGrouping"):
				um.beginUndoGrouping()
				return um

	except Exception:
		pass

	return None


def end_doc_undo_group(um):
	try:
		if um and hasattr(um, "endUndoGrouping"):
			um.endUndoGrouping()

	except Exception:
		pass


def outer_asc_desc(masters):
	"""
	Return the highest Ascender and lowest Descender
	across the supplied masters.
	"""
	ascValues = []
	descValues = []

	for m in masters:
		try:
			ascValues.append(float(getattr(m, "ascender", 0.0)))
			descValues.append(float(getattr(m, "descender", 0.0)))
		except Exception:
			pass

	asc = max(ascValues) if ascValues else 0.0
	desc = min(descValues) if descValues else 0.0

	return asc, desc


def clear_master_metric_overrides(font, clearWin=False, clearTypoHhea=False, clearUseTypo=False):
	"""
	Font-level vertical metric parameters should not be shadowed by
	Master-level versions of the same parameters.

	When writing Font-level metrics, remove matching parameters
	from every master in the font.
	"""
	for m in (font.masters or []):

		if clearWin:
			remove_param(m, "winAscent")
			remove_param(m, "winDescent")

		if clearTypoHhea:
			remove_param(m, "typoAscender")
			remove_param(m, "typoDescender")
			remove_param(m, "typoLineGap")

			remove_param(m, "hheaAscender")
			remove_param(m, "hheaDescender")
			remove_param(m, "hheaLineGap")

		if clearUseTypo:
			remove_param(m, "Use Typo Metrics")


# ---------- parametric processing ----------

def compute_extremes(font, masters, glyphs, progress=False):
	globalMaxY = None
	globalMinY = None
	scannedLayers = 0

	totalWork = max(1, len(masters) * len(glyphs))
	step = max(300, int(totalWork / 15))
	work = 0

	for m in masters:
		mid = m.id

		for g in glyphs:
			work += 1

			if progress and (work % step == 0):
				print(f"… scanning {work}/{totalWork}")

			try:
				L = g.layers[mid]
			except Exception:
				L = None

			b = get_layer_bounds(L)

			if not b:
				continue

			minY, maxY = b
			scannedLayers += 1

			if globalMaxY is None or maxY > globalMaxY:
				globalMaxY = maxY

			if globalMinY is None or minY < globalMinY:
				globalMinY = minY

	return globalMinY, globalMaxY, scannedLayers


def compute_linegap(asc, desc, pct, doRound=True):
	total = float(asc) + abs(float(desc))
	gap = total * (pct / 100.0)

	return round_int(gap) if doRound else int(round(gap))


# ---------- make an interface ----------

class VerticalMetricsUI(object):

	def __init__(self):

		self.w = Window((470, 610), "Vertical Metrics Helper")

		y = 12

		# CLUSTER 1: Scope

		self.w.scopeTitle = TextBox(
			(12, y, -12, 16),
			"SCOPE",
			sizeStyle="small",
		)
		y += 18

		self.w.masterLabel = TextBox(
			(12, y, 160, 18),
			"Masters:",
			sizeStyle="small",
		)

		self.w.masterScope = PopUpButton(
			(172, y, -12, 20),
			[
				"Current master",
				"All masters",
			],
			sizeStyle="small",
		)

		y += 26

		self.w.glyphLabel = TextBox(
			(12, y, 160, 18),
			"Scan glyphs:",
			sizeStyle="small",
		)

		self.w.glyphScope = PopUpButton(
			(172, y, -12, 20),
			[
				"All exportable glyphs",
				"Selected glyphs only",
			],
			sizeStyle="small",
		)

		y += 26

		self.w.sep1 = HorizontalLine((12, y, -12, 1))
		y += 12

		# CLUSTER 2: Strategy & values

		self.w.strategyTitle = TextBox(
			(12, y, -12, 16),
			"STRATEGY",
			sizeStyle="small",
		)

		y += 18

		self.w.strategyLabel = TextBox(
			(12, y, 160, 18),
			"Metric Recipe:",
			sizeStyle="small",
		)

		self.w.strategy = PopUpButton(
			(172, y, -12, 20),
			[
				"Recommended",
				"All from extremes (win + typo/hhea)",
				"All from Asc/Desc (win + typo/hhea)",
			],
			sizeStyle="small",
			callback=self.updateStrategyNote,
		)

		y += 26

		self.w.strategyNote = TextBox(
			(12, y, -12, 34),
			"Recommended: win from extremes; typo/hhea from selected masters’ outer Asc/Desc.",
			sizeStyle="small",
		)

		y += 36

		self.w.lineGapLabel = TextBox(
			(12, y, 160, 22),
			"Line Gap %:",
			sizeStyle="small",
		)

		self.w.lineGapPct = EditText(
			(172, y, 60, 18),
			"10",
			sizeStyle="small",
		)

		self.w.lineGapHint = TextBox(
			(238, y, -12, 18),
			"Typical: 10–20.",
			sizeStyle="small",
		)

		y += 28

		self.w.roundWin = CheckBox(
			(12, y, -12, 20),
			"Round winAscent/winDescent up to integers.",
			value=True,
			sizeStyle="small",
		)

		y += 22

		self.w.roundGap = CheckBox(
			(12, y, -12, 20),
			"Round LineGaps to integers.",
			value=True,
			sizeStyle="small",
		)

		y += 26

		self.w.sep2 = HorizontalLine((12, y, -12, 1))
		y += 12

		# CLUSTER 3: Output

		self.w.outTitle = TextBox(
			(12, y, -12, 16),
			"OUTPUT",
			sizeStyle="small",
		)

		y += 18

		self.w.enableUseTypo = CheckBox(
			(12, y, -12, 20),
			"Set Font Custom Parameter: Use Typo Metrics = yes",
			value=True,
			sizeStyle="small",
		)

		y += 22

		self.w.writeWin = CheckBox(
			(12, y, -12, 20),
			"Write winAscent / winDescent (Font-level parameters).",
			value=True,
			sizeStyle="small",
		)

		y += 22

		self.w.writeTypoHhea = CheckBox(
			(12, y, -12, 20),
			"Write typo/hhea + LineGaps (Font-level parameters).",
			value=True,
			sizeStyle="small",
		)

		y += 26

		self.w.sep3 = HorizontalLine((12, y, -12, 1))
		y += 12

		# CLUSTER 4: Preview

		self.w.prevTitle = TextBox(
			(12, y, -12, 16),
			"PREVIEW",
			sizeStyle="small",
		)

		y += 18

		self.w.preview = TextEditor(
			(12, y, -12, 96),
			text="Click Preview to compute values for the current settings.",
		)

		try:
			ns = self.w.preview.getNSTextView()
			ns.setEditable_(False)
			ns.setSelectable_(True)
			ns.setDrawsBackground_(True)
			ns.setBackgroundColor_(NSColor.whiteColor())
		except Exception:
			pass

		y += 106

		# Buttons

		btnY = y
		btnW = 106
		gap = 16
		x0 = 12

		self.w.previewBtn = Button(
			(x0 + (btnW + gap) * 0, btnY, btnW, 32),
			"Preview",
			callback=self.previewValues,
		)

		self.w.runBtn = Button(
			(x0 + (btnW + gap) * 1, btnY, btnW, 32),
			"Run 🏁",
			callback=self.run,
		)

		self.w.resetBtn = Button(
			(x0 + (btnW + gap) * 2, btnY, btnW, 32),
			"Reset ⌘Z",
			callback=self.reset,
		)

		y += 44

		x, yy, w, h = self.w.getPosSize()
		self.w.resize(w, y)

		self.updateStrategyNote(None)
		self.w.open()


	def updateStrategyNote(self, sender):

		i = self.w.strategy.get()

		if i == 0:
			txt = "Recommended: win from extremes; typo/hhea from selected masters’ outer Asc/Desc."

		elif i == 1:
			txt = "All from extremes: safest against clipping (more padding / less tight)."

		else:
			txt = "All from Asc/Desc: respects design metrics (can clip tall marks if Asc/Desc are tight)."

		self.w.strategyNote.set(txt)


	def _collect_scope(self):

		global Font
		Font = Glyphs.font

		if not Font:
			return None, None, "⚠️ No font open."

		masterScope = self.w.masterScope.get()

		if masterScope == 0:
			masters = [Font.selectedFontMaster] if Font.selectedFontMaster else []
		else:
			masters = master_list(Font)

		masters = [m for m in masters if m is not None]

		if not masters:
			return None, None, "⚠️ No masters found."

		glyphScope = self.w.glyphScope.get()

		if glyphScope == 0:
			glyphs = exportable_glyphs(Font)
		else:
			glyphs = selected_glyphs(Font)

		if not glyphs:
			return None, None, "⚠️ No glyphs to scan."

		return masters, glyphs, None


	def previewValues(self, sender):

		masters, glyphs, err = self._collect_scope()

		if err:
			self.w.preview.set(err)
			print(err)
			return

		lineGapPct = clamp(
			parseFloat(self.w.lineGapPct.get(), 10.0),
			0.0,
			100.0,
		)

		roundWinUp = bool(self.w.roundWin.get())
		roundGap = bool(self.w.roundGap.get())
		strategy = self.w.strategy.get()

		minY, maxY, scannedLayers = compute_extremes(
			Font,
			masters,
			glyphs,
			progress=False,
		)

		if minY is None or maxY is None:
			msg = "⚠️ Preview failed: could not measure bounds."
			self.w.preview.set(msg)
			print(msg)
			return

		winA = max(0.0, float(maxY))
		winD = max(0.0, float(-minY))

		if roundWinUp:
			winA = ceil_int(winA)
			winD = ceil_int(winD)
		else:
			winA = round_int(winA)
			winD = round_int(winD)

		outerAsc, outerDesc = outer_asc_desc(masters)

		if strategy == 1:
			typoAsc = float(winA)
			typoDesc = float(-winD)
		else:
			typoAsc = outerAsc
			typoDesc = outerDesc

		if strategy == 2:
			previewWinA = round_int(max(0.0, outerAsc))
			previewWinD = round_int(abs(min(0.0, outerDesc)))
		else:
			previewWinA = int(winA)
			previewWinD = int(winD)

		gap = compute_linegap(
			typoAsc,
			typoDesc,
			lineGapPct,
			doRound=roundGap,
		)

		lines = []

		lines.append(
			f"Scanned: {len(glyphs)} glyph(s), "
			f"{scannedLayers} measured layer(s)"
		)

		lines.append(
			f"Extremes: maxY={round_int(maxY)}, "
			f"minY={round_int(minY)}"
		)

		lines.append(
			f"winAscent={int(previewWinA)}  "
			f"winDescent={int(previewWinD)}"
		)

		lines.append(
			f"typo/hhea: Asc={round_int(typoAsc)}  "
			f"Desc={round_int(typoDesc)}  "
			f"LineGap={int(gap)}"
		)

		if strategy == 0:
			lines.append(
				"Recipe: Recommended "
				"(win extremes; typo/hhea from outer Asc/Desc)"
			)

		elif strategy == 1:
			lines.append(
				"Recipe: All from extremes"
			)

		else:
			lines.append(
				"Recipe: All from Asc/Desc"
			)

		self.w.preview.set("\n".join(lines))


	def reset(self, sender):

		global Font
		Font = Glyphs.font

		if not Font:
			return

		doc_undo_once(Font)

		try:
			if Font.currentTab:
				Font.currentTab.redraw()

			Glyphs.redraw()

		except Exception:
			pass


	def run(self, sender):

		global Font
		Font = Glyphs.font

		if not Font:
			print("⚠️ No font open.")
			return

		masters, glyphs, err = self._collect_scope()

		if err:
			print(err)
			return

		lineGapPct = clamp(
			parseFloat(self.w.lineGapPct.get(), 10.0),
			0.0,
			100.0,
		)

		roundWinUp = bool(self.w.roundWin.get())
		roundGap = bool(self.w.roundGap.get())

		doUseTypo = bool(self.w.enableUseTypo.get())
		doWin = bool(self.w.writeWin.get())
		doTypoHhea = bool(self.w.writeTypoHhea.get())

		strategy = self.w.strategy.get()

		if not (doUseTypo or doWin or doTypoHhea):
			print("ℹ️ Nothing to write (all output options unchecked).")
			return

		Font.disableUpdateInterface()
		um = begin_doc_undo_group(Font)

		try:

			minY, maxY, scannedLayers = compute_extremes(
				Font,
				masters,
				glyphs,
				progress=True,
			)

			if minY is None or maxY is None:
				print(
					"⚠️ Could not measure bounds "
					"(no drawable layers found)."
				)
				return

			winAscent = max(0.0, float(maxY))
			winDescent = max(0.0, float(-minY))

			if roundWinUp:
				winAscent = ceil_int(winAscent)
				winDescent = ceil_int(winDescent)
			else:
				winAscent = round_int(winAscent)
				winDescent = round_int(winDescent)

			outerAsc, outerDesc = outer_asc_desc(masters)

			# ----------------------------------------------------------
			# Clear matching Master-level overrides.
			# Font-level parameters should be authoritative.
			# ----------------------------------------------------------

			clear_master_metric_overrides(
				Font,
				clearWin=doWin,
				clearTypoHhea=doTypoHhea,
				clearUseTypo=doUseTypo,
			)

			# ----------------------------------------------------------
			# Use Typo Metrics
			# ----------------------------------------------------------

			if doUseTypo:
				set_param(
					Font,
					"Use Typo Metrics",
					True,
				)

			# ----------------------------------------------------------
			# winAscent / winDescent
			# ----------------------------------------------------------

			if doWin:

				if strategy == 2:
					# All from Asc/Desc
					winA = int(
						round_int(
							max(0.0, outerAsc)
						)
					)

					winD = int(
						round_int(
							abs(min(0.0, outerDesc))
						)
					)

				else:
					# Recommended / All from extremes
					winA = int(winAscent)
					winD = int(winDescent)

				set_param(
					Font,
					"winAscent",
					winA,
				)

				set_param(
					Font,
					"winDescent",
					winD,
				)

			# ----------------------------------------------------------
			# typo + hhea
			# ----------------------------------------------------------

			if doTypoHhea:

				if strategy == 1:
					# All from extremes
					asc = float(winAscent)
					desc = float(-winDescent)

				else:
					# Recommended / All from Asc/Desc
					asc = float(outerAsc)
					desc = float(outerDesc)

				gap = compute_linegap(
					asc,
					desc,
					lineGapPct,
					doRound=roundGap,
				)

				ascI = round_int(asc)
				descI = round_int(desc)

				set_param(
					Font,
					"typoAscender",
					int(ascI),
				)

				set_param(
					Font,
					"typoDescender",
					int(descI),
				)

				set_param(
					Font,
					"typoLineGap",
					int(gap),
				)

				set_param(
					Font,
					"hheaAscender",
					int(ascI),
				)

				set_param(
					Font,
					"hheaDescender",
					int(descI),
				)

				set_param(
					Font,
					"hheaLineGap",
					int(gap),
				)

		finally:

			end_doc_undo_group(um)
			Font.enableUpdateInterface()

			try:
				if Font.currentTab:
					Font.currentTab.redraw()

				Glyphs.redraw()

			except Exception:
				pass

		masterNames = ", ".join(
			[m.name for m in masters]
		)

		glyphMsg = (
			"exportable glyphs"
			if self.w.glyphScope.get() == 0
			else "selected glyphs"
		)

		print("✔ Vertical Metrics Helper")
		print(f"→ Masters scanned: {masterNames}")
		print(f"→ Scanned: {len(glyphs)} {glyphMsg}")

		if doWin:
			print(
				"→ winAscent/winDescent written at Font level"
			)

		if doTypoHhea:
			print(
				f"→ typo/hhea written at Font level; "
				f"LineGap={lineGapPct}% of (Asc+|Desc|)"
			)

		if doUseTypo:
			print(
				"→ Use Typo Metrics = yes"
			)

		if doWin or doTypoHhea or doUseTypo:
			print(
				"→ Matching Master-level overrides removed"
			)

		print("✅ Done.")


VerticalMetricsUI()