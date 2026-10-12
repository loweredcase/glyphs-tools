#MenuTitle: Position Builder
# -*- coding: utf-8 -*-
__doc__ = """
Generates a reliable positional OpenType feature for isolated / initial / medial / final glyph systems in Glyphs 4.
"""


# --------------------------------------------------------
# Addition Projects - Last Update, Oct 12 2026
# --------------------------------------------------------
# Glyph Tools: Position Builder
# --------------------------------------------------------
# → Detects complete positional glyph sets
# → Supports customizable suffixes
# → Supports a customizable target OpenType feature
# → Generates synchronized positional classes
# → Handles runs of 1, 2, 3, 4+ participating glyphs
# → Preserves unrelated code in the target feature
# → Safely updates its own generated lookups when rerun
# → Reports incomplete positional sets
# --------------------------------------------------------


import re

from GlyphsApp import Glyphs, GSClass, GSFeature
from AppKit import NSColor
from vanilla import (
	Window,
	TextBox,
	EditText,
	Button,
	HorizontalLine,
	TextEditor,
)


# --------------------------------------------------------------------
# Generated class names
# --------------------------------------------------------------------

CLASS_DEFAULT = "posDefault"
CLASS_ISOL = "posIsol"
CLASS_INIT = "posInit"
CLASS_MEDI = "posMedi"
CLASS_FINA = "posFina"


# --------------------------------------------------------------------
# Generated lookup names
# --------------------------------------------------------------------

LOOKUP_NAMES = [
	"positional_medi",
	"positional_long_edges",
	"positional_pair_init",
	"positional_pair_fina",
	"positional_isol",
]


# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------

def clean_string(value):
	try:
		return str(value).strip()
	except Exception:
		return ""


def valid_feature_tag(tag):
	if len(tag) != 4:
		return False

	for char in tag:
		if not (char.isalpha() or char.isdigit()):
			return False

	return True


def glyph_names(font):
	return set(
		glyph.name
		for glyph in font.glyphs
		if glyph and glyph.name
	)


def get_feature(font, tag):
	try:
		return font.features[tag]
	except Exception:
		return None


def set_class(font, name, code):
	"""
	Create or update one generated positional class.
	"""

	theClass = font.classes[name]

	if theClass:
		theClass.code = code
		theClass.automatic = False

	else:
		theClass = GSClass(name, code)
		theClass.automatic = False
		font.classes.append(theClass)


def analyze_sets(font, suffixes):
	"""
	Find complete and incomplete positional families
	in font glyph order.
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
	orphanBases = {}

	# ------------------------------------------------------------
	# Base glyphs with positional forms
	# ------------------------------------------------------------

	for glyph in font.glyphs:

		if not glyph or not glyph.name:
			continue

		base = glyph.name

		# Do not treat positional alternates themselves as bases.
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

		# No positional forms = ordinary non-participating glyph.
		if not present:
			continue

		if not missing:
			complete.append(base)

		else:
			incomplete.append(
				(base, missing)
			)

	# ------------------------------------------------------------
	# Positional forms whose base glyph does not exist
	# ------------------------------------------------------------

	for glyph in font.glyphs:

		if not glyph or not glyph.name:
			continue

		name = glyph.name

		for role, suffix in roles:

			if not name.endswith(suffix):
				continue

			base = name[:-len(suffix)]

			if not base:
				continue

			if base not in names:

				if base not in orphanBases:
					orphanBases[base] = set()

				orphanBases[base].add(role)

	orphans = []

	for base, foundRoles in orphanBases.items():

		orphans.append(
			(
				base,
				sorted(foundRoles),
			)
		)

	return complete, incomplete, orphans


def build_class_codes(completeBases, suffixes):
	"""
	Build all five classes from exactly the same
	base-glyph order.
	"""

	return {
		CLASS_DEFAULT:
			" ".join(completeBases),

		CLASS_ISOL:
			" ".join(
				base + suffixes["isol"]
				for base in completeBases
			),

		CLASS_INIT:
			" ".join(
				base + suffixes["init"]
				for base in completeBases
			),

		CLASS_MEDI:
			" ".join(
				base + suffixes["medi"]
				for base in completeBases
			),

		CLASS_FINA:
			" ".join(
				base + suffixes["fina"]
				for base in completeBases
			),
	}


def generated_feature_code():
	"""
	Return only the actual generated OpenType code.
	No metadata/header comments are inserted.
	"""

	return f"""\
lookup positional_medi {{
	lookupflag IgnoreMarks;

	sub @{CLASS_DEFAULT} @{CLASS_DEFAULT}' @{CLASS_DEFAULT} by @{CLASS_MEDI};
	sub @{CLASS_MEDI} @{CLASS_DEFAULT}' @{CLASS_DEFAULT} by @{CLASS_MEDI};
}} positional_medi;


lookup positional_long_edges {{
	lookupflag IgnoreMarks;

	sub @{CLASS_DEFAULT}' @{CLASS_MEDI} by @{CLASS_INIT};
	sub @{CLASS_MEDI} @{CLASS_DEFAULT}' by @{CLASS_FINA};
}} positional_long_edges;


lookup positional_pair_init {{
	lookupflag IgnoreMarks;

	sub @{CLASS_DEFAULT}' @{CLASS_DEFAULT} by @{CLASS_INIT};
}} positional_pair_init;


lookup positional_pair_fina {{
	lookupflag IgnoreMarks;

	sub @{CLASS_INIT} @{CLASS_DEFAULT}' by @{CLASS_FINA};
}} positional_pair_fina;


lookup positional_isol {{
	lookupflag IgnoreMarks;

	sub @{CLASS_DEFAULT} by @{CLASS_ISOL};
}} positional_isol;"""


def strip_generated_lookups(code):
	"""
	Remove only the lookups generated by this tool.

	Unrelated feature code is preserved.
	"""

	code = code or ""

	for lookupName in LOOKUP_NAMES:

		pattern = (
			r"\s*"
			r"lookup\s+"
			+ re.escape(lookupName)
			+ r"\s*\{"
			+ r".*?"
			+ r"\}\s*"
			+ re.escape(lookupName)
			+ r"\s*;"
		)

		code = re.sub(
			pattern,
			"",
			code,
			flags=re.DOTALL,
		)

	return code.strip()


def compile_font_features(font):
	try:
		font.compileFeatures()
		return True, None

	except Exception as error:
		return False, error


# --------------------------------------------------------------------
# UI
# --------------------------------------------------------------------

class PositionalFeatureMakerUI(object):

	def __init__(self):

		self.W = 540

		self.w = Window(
			(self.W, 560),
			"Positional Feature Maker",
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
			(12, y, 150, 18),
			"Isolated suffix:",
			sizeStyle="small",
		)

		self.w.isolSuffixField = EditText(
			(162, y, -12, 22),
			".isol",
			sizeStyle="small",
		)

		y += 28

		self.w.initLabel = TextBox(
			(12, y, 150, 18),
			"Initial suffix:",
			sizeStyle="small",
		)

		self.w.initSuffixField = EditText(
			(162, y, -12, 22),
			".init",
			sizeStyle="small",
		)

		y += 28

		self.w.mediLabel = TextBox(
			(12, y, 150, 18),
			"Medial suffix:",
			sizeStyle="small",
		)

		self.w.mediSuffixField = EditText(
			(162, y, -12, 22),
			".medi",
			sizeStyle="small",
		)

		y += 28

		self.w.finaLabel = TextBox(
			(12, y, 150, 18),
			"Final suffix:",
			sizeStyle="small",
		)

		self.w.finaSuffixField = EditText(
			(162, y, -12, 22),
			".fina",
			sizeStyle="small",
		)

		y += 30

		self.w.sep1 = HorizontalLine(
			(12, y, -12, 1)
		)

		y += 12

		# ------------------------------------------------------------
		# Feature
		# ------------------------------------------------------------

		self.w.featureTitle = TextBox(
			(12, y, -12, 16),
			"FEATURE",
			sizeStyle="small",
		)

		y += 20

		self.w.featureLabel = TextBox(
			(12, y, 150, 18),
			"OpenType feature:",
			sizeStyle="small",
		)

		self.w.featureTagField = EditText(
			(162, y, 70, 22),
			"calt",
			sizeStyle="small",
		)

		self.w.featureHint = TextBox(
			(242, y, -12, 18),
			"4-character tag, e.g. calt, rlig, ss01",
			sizeStyle="small",
		)

		y += 30

		self.w.classHint = TextBox(
			(12, y, -12, 30),
			"Generates positional classes automatically. Rerun safely to update them as the font is drawn.",
			sizeStyle="small",
		)

		y += 34

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
			(12, y, -12, 190),
			text="Click Preview to find complete and incomplete positional sets.",
		)

		try:
			ns = self.w.previewBox.getNSTextView()
			ns.setEditable_(False)
			ns.setSelectable_(True)
			ns.setDrawsBackground_(True)
			ns.setBackgroundColor_(
				NSColor.whiteColor()
			)
		except Exception:
			pass

		y += 202

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
			callback=self.previewSets,
		)

		self.w.generateButton = Button(
			(
				left + btnW + gap,
				y,
				btnW,
				btnH,
			),
			"Generate / Update 🏁",
			callback=self.generate,
		)

		y += 44

		# Trim window

		x, yy, w, h = self.w.getPosSize()
		self.w.resize(w, y)

		self.w.open()


	# ------------------------------------------------------------
	# Settings
	# ------------------------------------------------------------

	def getSettings(self):

		suffixes = {
			"isol": clean_string(
				self.w.isolSuffixField.get()
			),

			"init": clean_string(
				self.w.initSuffixField.get()
			),

			"medi": clean_string(
				self.w.mediSuffixField.get()
			),

			"fina": clean_string(
				self.w.finaSuffixField.get()
			),
		}

		featureTag = clean_string(
			self.w.featureTagField.get()
		).lower()

		values = list(
			suffixes.values()
		)

		if not all(values):

			return (
				None,
				None,
				"⚠️ All four suffix fields must contain a value.",
			)

		if len(set(values)) != 4:

			return (
				None,
				None,
				"⚠️ The four positional suffixes must be different.",
			)

		if not valid_feature_tag(
			featureTag
		):

			return (
				None,
				None,
				"⚠️ Feature tag must contain exactly four letters or numbers.",
			)

		return (
			suffixes,
			featureTag,
			None,
		)


	# ------------------------------------------------------------
	# Report
	# ------------------------------------------------------------

	def buildReport(
		self,
		font,
		suffixes,
		featureTag,
		complete,
		incomplete,
		orphans,
	):

		lines = []

		lines.append(
			f"Feature: {featureTag}"
		)

		lines.append(
			"Suffixes: "
			f"{suffixes['isol']} / "
			f"{suffixes['init']} / "
			f"{suffixes['medi']} / "
			f"{suffixes['fina']}"
		)

		lines.append("")

		lines.append(
			f"Complete positional sets: {len(complete)}"
		)

		if complete:

			lines.append(
				"  "
				+ " ".join(complete)
			)

		else:

			lines.append(
				"  None found."
			)

		if incomplete:

			lines.append("")
			lines.append(
				f"Incomplete sets: {len(incomplete)}"
			)

			for base, missing in incomplete:

				lines.append(
					f"  {base} — missing "
					+ ", ".join(missing)
				)

		if orphans:

			lines.append("")
			lines.append(
				"Alternates with no matching base glyph:"
			)

			for base, foundRoles in orphans:

				lines.append(
					f"  {base} — found "
					+ ", ".join(foundRoles)
					+ "; base missing"
				)

		targetFeature = get_feature(
			font,
			featureTag,
		)

		if (
			targetFeature
			and getattr(
				targetFeature,
				"automatic",
				False,
			)
		):

			lines.append("")
			lines.append(
				f"⚠️ Feature '{featureTag}' is currently Automatic."
			)

			lines.append(
				"Make it manual before generating."
			)

		return "\n".join(lines)


	# ------------------------------------------------------------
	# Preview
	# ------------------------------------------------------------

	def previewSets(self, sender):

		font = Glyphs.font

		if not font:

			self.w.previewBox.set(
				"⚠️ No font open."
			)

			return

		(
			suffixes,
			featureTag,
			error,
		) = self.getSettings()

		if error:

			self.w.previewBox.set(
				error
			)

			return

		(
			complete,
			incomplete,
			orphans,
		) = analyze_sets(
			font,
			suffixes,
		)

		report = self.buildReport(
			font,
			suffixes,
			featureTag,
			complete,
			incomplete,
			orphans,
		)

		self.w.previewBox.set(
			report
		)


	# ------------------------------------------------------------
	# Generate
	# ------------------------------------------------------------

	def generate(self, sender):

		font = Glyphs.font

		if not font:

			self.w.previewBox.set(
				"⚠️ No font open."
			)

			return

		(
			suffixes,
			featureTag,
			error,
		) = self.getSettings()

		if error:

			self.w.previewBox.set(
				error
			)

			return

		(
			complete,
			incomplete,
			orphans,
		) = analyze_sets(
			font,
			suffixes,
		)

		if not complete:

			self.w.previewBox.set(
				"⚠️ No complete positional sets found.\n\n"
				"Each participating base needs all four "
				"positional forms."
			)

			return

		# --------------------------------------------------------
		# Do not write into an automatic target feature.
		# --------------------------------------------------------

		targetFeature = get_feature(
			font,
			featureTag,
		)

		if (
			targetFeature
			and getattr(
				targetFeature,
				"automatic",
				False,
			)
		):

			self.w.previewBox.set(
				f"⚠️ Feature '{featureTag}' is Automatic.\n\n"
				"Make the feature manual first, then run "
				"Positional Feature Maker again."
			)

			return

		# --------------------------------------------------------
		# Update positional classes
		# --------------------------------------------------------

		classCodes = build_class_codes(
			complete,
			suffixes,
		)

		for className, code in classCodes.items():

			set_class(
				font,
				className,
				code,
			)

		# --------------------------------------------------------
		# Remove previous generated lookups from every feature.
		#
		# This allows calt → rlig, etc. without leaving
		# the old positional logic behind.
		# --------------------------------------------------------

		for feature in font.features:

			feature.code = (
				strip_generated_lookups(
					feature.code
				)
			)

		# --------------------------------------------------------
		# Create / update target feature
		# --------------------------------------------------------

		targetFeature = get_feature(
			font,
			featureTag,
		)

		block = generated_feature_code()

		if not targetFeature:

			targetFeature = GSFeature(
				featureTag,
				block,
			)

			targetFeature.automatic = False

			font.features.append(
				targetFeature
			)

		else:

			existing = (
				targetFeature.code or ""
			).strip()

			if existing:

				targetFeature.code = (
					existing
					+ "\n\n"
					+ block
				)

			else:

				targetFeature.code = block

			targetFeature.automatic = False

		# --------------------------------------------------------
		# Compile
		# --------------------------------------------------------

		ok, compileError = (
			compile_font_features(
				font
			)
		)

		if not ok:

			self.w.previewBox.set(
				"❌ Generated the classes and feature code, "
				"but Glyphs reported a feature compilation error:\n\n"
				+ str(compileError)
			)

			print(
				"❌ Positional Feature Maker"
			)

			print(
				compileError
			)

			return

		# --------------------------------------------------------
		# Success report
		# --------------------------------------------------------

		report = self.buildReport(
			font,
			suffixes,
			featureTag,
			complete,
			incomplete,
			orphans,
		)

		report += (
			"\n\n"
			f"✅ Updated @{CLASS_DEFAULT}, "
			f"@{CLASS_ISOL}, "
			f"@{CLASS_INIT}, "
			f"@{CLASS_MEDI}, "
			f"@{CLASS_FINA}"
			"\n"
			f"✅ Generated positional code in '{featureTag}'."
		)

		self.w.previewBox.set(
			report
		)

		print(
			"✔ Positional Feature Maker"
		)

		print(
			f"→ Feature: {featureTag}"
		)

		print(
			f"→ Complete sets: {len(complete)}"
		)

		if incomplete:

			print(
				f"→ Incomplete sets omitted: {len(incomplete)}"
			)

		print(
			"✅ Done."
		)


PositionalFeatureMakerUI()