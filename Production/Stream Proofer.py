#MenuTitle: Streamer Proofer
# -*- coding: utf-8 -*-
__doc__ = """
Builds structured proof tabs for positional/contextual glyph systems.
"""


# --------------------------------------------------------------------
# Addition Projects - Last Update, Oct 22 2026
# --------------------------------------------------------------------
# Glyph Tools: Streamer Proofer
# --------------------------------------------------------------------
# → Detect complete isolated / initial / medial / final glyph sets
# → Proof literal positional forms or contextual feature behavior
# → Customizable suffixes and OpenType feature
# → Report incomplete positional sets before opening a proof
# → Proof all complete sets or selected positional families
# --------------------------------------------------------------------


from GlyphsApp import Glyphs
from AppKit import NSColor
from vanilla import (
	Window,
	TextBox,
	EditText,
	Button,
	PopUpButton,
	HorizontalLine,
	TextEditor,
)


# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------

def clean_string(value):
	try:
		return str(value).strip()
	except Exception:
		return ""


def parse_int(value, fallback=0):
	try:
		return int(str(value).strip())
	except Exception:
		return fallback


def glyph_names(font):
	return set(
		glyph.name
		for glyph in font.glyphs
		if glyph and glyph.name
	)


def slash(name):
	return "/" + name


def spaces(count):
	return " " * max(1, count)


def analyze_sets(font, suffixes):
	"""
	Return:
	- complete positional base glyphs in font order
	- incomplete sets and their missing forms
	"""

	names = glyph_names(font)

	roles = [
		("isol", suffixes["isol"]),
		("init", suffixes["init"]),
		("medi", suffixes["medi"]),
		("fina", suffixes["fina"]),
	]

	allSuffixes = [
		suffix
		for role, suffix in roles
	]

	complete = []
	incomplete = []

	for glyph in font.glyphs:

		if not glyph or not glyph.name:
			continue

		base = glyph.name

		# Positional forms themselves are not treated as bases.
		if any(
			base.endswith(suffix)
			for suffix in allSuffixes
		):
			continue

		present = []
		missing = []

		for role, suffix in roles:

			alternateName = base + suffix

			if alternateName in names:
				present.append(role)
			else:
				missing.append(suffix)

		# No positional forms at all:
		# ordinary, non-participating glyph.
		if not present:
			continue

		if not missing:
			complete.append(base)

		else:
			incomplete.append(
				(base, missing)
			)

	return complete, incomplete


def selected_base_names(
	font,
	complete,
	suffixes,
):
	"""
	A selected base OR any of its positional forms counts
	as selecting the whole positional family.
	"""

	completeSet = set(complete)
	selected = set()

	allSuffixes = [
		suffixes["isol"],
		suffixes["init"],
		suffixes["medi"],
		suffixes["fina"],
	]

	for layer in font.selectedLayers or []:

		try:
			name = layer.parent.name
		except Exception:
			continue

		if name in completeSet:
			selected.add(name)
			continue

		for suffix in allSuffixes:

			if not name.endswith(suffix):
				continue

			base = name[:-len(suffix)]

			if base in completeSet:
				selected.add(base)

			break

	# Preserve font order.
	return [
		base
		for base in complete
		if base in selected
	]


# --------------------------------------------------------------------
# Proof builders
# --------------------------------------------------------------------

def build_forms_proof(
	bases,
	suffixes,
	medialRepeats,
	groupSpaces,
):
	"""
	Example:

	E  E.init E.medi E.medi E.fina  E.isol  E.medi

	Slash notation ensures the exact glyphs are placed.
	"""

	gap = spaces(groupSpaces)

	lines = []

	for base in bases:

		stream = (
			slash(
				base
				+ suffixes["init"]
			)
			+ (
				slash(
					base
					+ suffixes["medi"]
				)
				* medialRepeats
			)
			+ slash(
				base
				+ suffixes["fina"]
			)
		)

		line = (
			slash(base)
			+ gap
			+ stream
			+ gap
			+ slash(
				base
				+ suffixes["isol"]
			)
			+ gap
			+ slash(
				base
				+ suffixes["medi"]
			)
		)

		lines.append(line)

	return "\n".join(lines)


def build_behavior_proof(
	bases,
	groupSpaces,
):
	"""
	Proof base glyphs only, so the selected OpenType feature
	must create the positional behavior.

	Example:

	E  EE  EEE  EEEE
	"""

	gap = spaces(groupSpaces)

	lines = []

	for base in bases:

		one = slash(base)

		two = (
			slash(base)
			+ slash(base)
		)

		three = (
			slash(base)
			+ slash(base)
			+ slash(base)
		)

		four = (
			slash(base)
			+ slash(base)
			+ slash(base)
			+ slash(base)
		)

		lines.append(
			one
			+ gap
			+ two
			+ gap
			+ three
			+ gap
			+ four
		)

	# ------------------------------------------------------------
	# Mixed-character streams
	# ------------------------------------------------------------

	if len(bases) >= 2:

		def cycle(index):
			return bases[
				index % len(bases)
			]

		pair = (
			slash(cycle(0))
			+ slash(cycle(1))
		)

		triple = (
			slash(cycle(0))
			+ slash(cycle(1))
			+ slash(cycle(2))
		)

		quad = (
			slash(cycle(0))
			+ slash(cycle(1))
			+ slash(cycle(2))
			+ slash(cycle(3))
		)

		lines.append("")

		lines.append(
			pair
			+ gap
			+ triple
			+ gap
			+ quad
		)

	return "\n".join(lines)


def human_forms_example(
	base,
	suffixes,
	medialRepeats,
	groupSpaces,
):
	"""
	Readable preview rather than slash notation.
	"""

	gap = spaces(groupSpaces)

	streamNames = [
		base + suffixes["init"]
	]

	streamNames += [
		base + suffixes["medi"]
		for i in range(
			medialRepeats
		)
	]

	streamNames.append(
		base + suffixes["fina"]
	)

	return (
		base
		+ gap
		+ " ".join(streamNames)
		+ gap
		+ base
		+ suffixes["isol"]
		+ gap
		+ base
		+ suffixes["medi"]
	)


def human_behavior_example(
	base,
	groupSpaces,
):
	gap = spaces(groupSpaces)

	return (
		base
		+ gap
		+ base * 2
		+ gap
		+ base * 3
		+ gap
		+ base * 4
	)


# --------------------------------------------------------------------
# Interface
# --------------------------------------------------------------------

class StreamProoferUI(object):

	def __init__(self):

		self.W = 520

		self.w = Window(
			(self.W, 540),
			"Stream Proofer",
		)

		y = 12

		# ------------------------------------------------------------
		# Positional forms
		# ------------------------------------------------------------

		self.w.formsTitle = TextBox(
			(12, y, -12, 16),
			"POSITIONAL FORMS",
			sizeStyle="small",
		)

		y += 20

		self.w.isolLabel = TextBox(
			(12, y, 145, 18),
			"Isolated suffix:",
			sizeStyle="small",
		)

		self.w.isolSuffixField = EditText(
			(157, y, -12, 22),
			".isol",
			sizeStyle="small",
		)

		y += 28

		self.w.initLabel = TextBox(
			(12, y, 145, 18),
			"Initial suffix:",
			sizeStyle="small",
		)

		self.w.initSuffixField = EditText(
			(157, y, -12, 22),
			".init",
			sizeStyle="small",
		)

		y += 28

		self.w.mediLabel = TextBox(
			(12, y, 145, 18),
			"Medial suffix:",
			sizeStyle="small",
		)

		self.w.mediSuffixField = EditText(
			(157, y, -12, 22),
			".medi",
			sizeStyle="small",
		)

		y += 28

		self.w.finaLabel = TextBox(
			(12, y, 145, 18),
			"Final suffix:",
			sizeStyle="small",
		)

		self.w.finaSuffixField = EditText(
			(157, y, -12, 22),
			".fina",
			sizeStyle="small",
		)

		y += 30

		self.w.sep1 = HorizontalLine(
			(12, y, -12, 1)
		)

		y += 12

		# ------------------------------------------------------------
		# Proof settings
		# ------------------------------------------------------------

		self.w.proofTitle = TextBox(
			(12, y, -12, 16),
			"PROOF",
			sizeStyle="small",
		)

		y += 20

		self.w.typeLabel = TextBox(
			(12, y, 145, 18),
			"Proof type:",
			sizeStyle="small",
		)

		self.w.proofTypePopup = PopUpButton(
			(157, y, -12, 22),
			[
				"Forms",
				"Feature behavior",
			],
			sizeStyle="small",
			callback=self.updateInterface,
		)

		y += 28

		self.w.scopeLabel = TextBox(
			(12, y, 145, 18),
			"Glyphs:",
			sizeStyle="small",
		)

		self.w.scopePopup = PopUpButton(
			(157, y, -12, 22),
			[
				"All complete sets",
				"Selected complete sets",
			],
			sizeStyle="small",
		)

		y += 28

		self.w.repeatLabel = TextBox(
			(12, y, 145, 18),
			"Medial repeats:",
			sizeStyle="small",
		)

		self.w.repeatField = EditText(
			(157, y, 60, 22),
			"2",
			sizeStyle="small",
		)

		self.w.repeatHint = TextBox(
			(227, y, -12, 18),
			"for the generated stream",
			sizeStyle="small",
		)

		y += 28

		self.w.spacingLabel = TextBox(
			(12, y, 145, 18),
			"Group spaces:",
			sizeStyle="small",
		)

		self.w.spacingField = EditText(
			(157, y, 60, 22),
			"2",
			sizeStyle="small",
		)

		y += 28

		self.w.featureLabel = TextBox(
			(12, y, 145, 18),
			"OpenType feature:",
			sizeStyle="small",
		)

		self.w.featureField = EditText(
			(157, y, 60, 22),
			"calt",
			sizeStyle="small",
		)

		self.w.featureHint = TextBox(
			(227, y, -12, 18),
			"used for Feature behavior",
			sizeStyle="small",
		)

		y += 32

		self.w.sep2 = HorizontalLine(
			(12, y, -12, 1)
		)

		y += 12

		# ------------------------------------------------------------
		# Preview
		# ------------------------------------------------------------

		self.w.previewTitle = TextBox(
			(12, y, -12, 16),
			"PREVIEW",
			sizeStyle="small",
		)

		y += 20

		self.w.previewBox = TextEditor(
			(12, y, -12, 120),
			text=(
				"Click Preview to find complete positional sets "
				"and inspect the proof structure."
			),
		)

		try:
			ns = (
				self.w.previewBox
				.getNSTextView()
			)

			ns.setEditable_(False)
			ns.setSelectable_(True)
			ns.setDrawsBackground_(True)

			ns.setBackgroundColor_(
				NSColor.whiteColor()
			)

		except Exception:
			pass

		y += 132

		self.w.sep3 = HorizontalLine(
			(12, y, -12, 1)
		)

		y += 14

		# ------------------------------------------------------------
		# Buttons
		# ------------------------------------------------------------

		left = 12
		right = 12
		gap = 16
		btnH = 32

		available = (
			self.W
			- left
			- right
			- gap
		)

		btnW = int(
			available / 2
		)

		self.w.previewButton = Button(
			(
				left,
				y,
				btnW,
				btnH,
			),
			"Preview",
			callback=self.previewProof,
		)

		self.w.runButton = Button(
			(
				left
				+ btnW
				+ gap,
				y,
				btnW,
				btnH,
			),
			"Run 🏁",
			callback=self.run,
		)

		y += 44

		# Trim window

		x, yy, w, h = (
			self.w.getPosSize()
		)

		self.w.resize(
			w,
			y,
		)

		self.updateInterface(None)

		self.w.open()


	# ------------------------------------------------------------
	# Dynamic interface
	# ------------------------------------------------------------

	def updateInterface(
		self,
		sender,
	):

		isForms = (
			self.w.proofTypePopup.get()
			== 0
		)

		# Medial repeat count matters only when
		# explicitly constructing the positional forms.
		self.w.repeatField.enable(
			isForms
		)

		self.w.repeatLabel.enable(
			isForms
		)

		self.w.repeatHint.enable(
			isForms
		)

		# Feature selection matters only when
		# testing contextual behavior.
		self.w.featureField.enable(
			not isForms
		)

		self.w.featureLabel.enable(
			not isForms
		)

		self.w.featureHint.enable(
			not isForms
		)


	# ------------------------------------------------------------
	# Settings
	# ------------------------------------------------------------

	def settings(self):

		suffixes = {
			"isol":
				clean_string(
					self.w
					.isolSuffixField
					.get()
				),

			"init":
				clean_string(
					self.w
					.initSuffixField
					.get()
				),

			"medi":
				clean_string(
					self.w
					.mediSuffixField
					.get()
				),

			"fina":
				clean_string(
					self.w
					.finaSuffixField
					.get()
				),
		}

		medialRepeats = max(
			0,
			parse_int(
				self.w
				.repeatField
				.get(),
				2,
			),
		)

		groupSpaces = max(
			1,
			parse_int(
				self.w
				.spacingField
				.get(),
				2,
			),
		)

		featureTag = clean_string(
			self.w
			.featureField
			.get()
		).lower()

		proofType = (
			self.w
			.proofTypePopup
			.get()
		)

		return (
			suffixes,
			medialRepeats,
			groupSpaces,
			featureTag,
			proofType,
		)


	# ------------------------------------------------------------
	# Analyze
	# ------------------------------------------------------------

	def analyze(self):

		font = Glyphs.font

		if not font:

			return (
				None,
				None,
				None,
				"⚠️ No font open.",
			)

		(
			suffixes,
			medialRepeats,
			groupSpaces,
			featureTag,
			proofType,
		) = self.settings()

		if not all(
			suffixes.values()
		):

			return (
				None,
				None,
				None,
				"⚠️ Enter all four positional suffixes.",
			)

		if len(
			set(
				suffixes.values()
			)
		) != 4:

			return (
				None,
				None,
				None,
				"⚠️ The four suffixes must be different.",
			)

		complete, incomplete = (
			analyze_sets(
				font,
				suffixes,
			)
		)

		if (
			self.w
			.scopePopup
			.get()
			== 1
		):

			bases = selected_base_names(
				font,
				complete,
				suffixes,
			)

			if not bases:

				return (
					None,
					complete,
					incomplete,
					"⚠️ No complete positional families selected.",
				)

		else:

			bases = complete

		if not bases:

			return (
				None,
				complete,
				incomplete,
				"⚠️ No complete positional sets found.",
			)

		return (
			bases,
			complete,
			incomplete,
			None,
		)


	# ------------------------------------------------------------
	# Preview
	# ------------------------------------------------------------

	def previewProof(
		self,
		sender,
	):

		(
			bases,
			complete,
			incomplete,
			error,
		) = self.analyze()

		if error:

			self.w.previewBox.set(
				error
			)

			return

		(
			suffixes,
			medialRepeats,
			groupSpaces,
			featureTag,
			proofType,
		) = self.settings()

		lines = []

		lines.append(
			f"Complete sets: {len(complete)}"
		)

		lines.append(
			"  "
			+ " ".join(
				complete
			)
		)

		if incomplete:

			lines.append("")

			lines.append(
				f"Incomplete sets: {len(incomplete)}"
			)

			for (
				base,
				missing,
			) in incomplete:

				lines.append(
					f"  {base} — missing "
					+ ", ".join(
						missing
					)
				)

		lines.append("")
		lines.append(
			"Proofing: "
			+ str(
				len(bases)
			)
			+ " set(s)"
		)

		lines.append("")

		firstBase = bases[0]

		if proofType == 0:

			lines.append(
				"Forms example:"
			)

			lines.append(
				"  "
				+ human_forms_example(
					firstBase,
					suffixes,
					medialRepeats,
					groupSpaces,
				)
			)

		else:

			lines.append(
				f"Feature behavior: {featureTag}"
			)

			lines.append(
				"  "
				+ human_behavior_example(
					firstBase,
					groupSpaces,
				)
			)

		self.w.previewBox.set(
			"\n".join(
				lines
			)
		)


	# ------------------------------------------------------------
	# Run
	# ------------------------------------------------------------

	def run(
		self,
		sender,
	):

		font = Glyphs.font

		(
			bases,
			complete,
			incomplete,
			error,
		) = self.analyze()

		if error:

			self.w.previewBox.set(
				error
			)

			return

		(
			suffixes,
			medialRepeats,
			groupSpaces,
			featureTag,
			proofType,
		) = self.settings()

		# --------------------------------------------------------
		# Forms
		# --------------------------------------------------------

		if proofType == 0:

			text = (
				build_forms_proof(
					bases,
					suffixes,
					medialRepeats,
					groupSpaces,
				)
			)

			tab = font.newTab(
				text
			)

			# Literal glyph forms:
			# do not reshape them through calt.
			try:
				tab.features = []
			except Exception:
				pass

		# --------------------------------------------------------
		# Feature behavior
		# --------------------------------------------------------

		else:

			if len(featureTag) != 4:

				self.w.previewBox.set(
					"⚠️ OpenType feature tag must be 4 characters."
				)

				return

			try:
				font.compileFeatures()

			except Exception as error:

				self.w.previewBox.set(
					"⚠️ Feature compilation failed.\n\n"
					+ str(error)
				)

				print("")
				print(
					"Stream Proofer — feature error:"
				)

				print(
					error
				)

				return

			text = (
				build_behavior_proof(
					bases,
					groupSpaces,
				)
			)

			tab = font.newTab(
				text
			)

			try:
				tab.features = [
					featureTag
				]

			except Exception:
				pass

		# Update Preview after running.
		self.previewProof(
			None
		)


StreamProoferUI()