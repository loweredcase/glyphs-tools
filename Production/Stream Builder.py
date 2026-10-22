#MenuTitle: Streamer Builder
# -*- coding: utf-8 -*-
__doc__ = """
Builds positional streamer glyphs (isol, init, medi, fina)
from selected, listed, or eligible base glyphs.
"""


# --------------------------------------------------------------------
# Addition Projects - Last Update, Oct 22 2026
# --------------------------------------------------------------------
# Glyph Tools: Streamer Builder
# --------------------------------------------------------------------
# → Builds positional streamer forms
# → Supports selected, all eligible, or listed source glyphs
# → Suggests underscore-prefixed component glyphs
# → Component fields remain fully editable
# → Optionally stretches middle components to medial width
# → Builds medial as middle component(s) behind the default glyph
# → Keeps middle component(s) anchored to the glyph origin
# → Shifts the default glyph inward by the added medial LSB
# → Adds configurable LSB / RSB space around the default glyph
# → Skips populated existing forms or rebuilds them explicitly
# → Preserves non-master special layers when rebuilding
# --------------------------------------------------------------------


from GlyphsApp import (
	Glyphs,
	GSGlyph,
	GSLayer,
	GSComponent,
)

from AppKit import NSColor
from Foundation import NSPoint

from vanilla import (
	Window,
	TextBox,
	EditText,
	Button,
	PopUpButton,
	HorizontalLine,
	TextEditor,
	ComboBox,
	CheckBox,
)


# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------

def clean_string(value):

	try:
		return str(value).strip()

	except Exception:
		return ""


def parse_number(
	value,
	fallback=0,
):

	try:
		return float(
			str(value).strip()
		)

	except Exception:
		return fallback


def nice_number(value):

	if int(value) == value:

		return str(
			int(value)
		)

	return str(
		round(
			value,
			2,
		)
	)


def signed_number(value):

	if value > 0:

		return (
			"+"
			+ nice_number(value)
		)

	return nice_number(
		value
	)


def parse_components(value):

	text = (
		clean_string(value)
		.replace(",", " ")
		.replace("\n", " ")
		.replace("\t", " ")
	)

	result = []

	for name in text.split():

		if name not in result:
			result.append(name)

	return result


def parse_glyph_list(value):

	text = clean_string(
		value
	)

	text = (
		text
		.replace(",", " ")
		.replace("\n", " ")
		.replace("\t", " ")
	)

	result = []

	for token in text.split():

		if "/" in token:

			parts = [
				part
				for part in token.split("/")
				if part
			]

		else:

			parts = [
				token
			]

		for name in parts:

			if name not in result:
				result.append(name)

	return result


def component_suggestions(font):

	if not font:
		return []

	return [
		glyph.name
		for glyph in font.glyphs
		if (
			glyph
			and glyph.name
			and glyph.name.startswith("_")
		)
	]


def get_master_layer(
	glyph,
	masterId,
):

	try:

		layer = glyph.layers[
			masterId
		]

	except Exception:

		layer = None

	if layer:
		return layer

	layer = GSLayer()

	layer.layerId = masterId
	layer.associatedMasterId = masterId

	glyph.layers[
		masterId
	] = layer

	return layer


def reset_master_layer(layer):

	try:

		layer.shapes = []

	except Exception:

		while len(
			layer.shapes
		):

			del layer.shapes[-1]

	try:

		layer.hints = []

	except Exception:

		while len(
			layer.hints
		):

			del layer.hints[-1]

	try:

		layer.leftMetricsKey = None
		layer.rightMetricsKey = None
		layer.widthMetricsKey = None

	except Exception:
		pass


def clear_glyph_metrics(glyph):

	for attribute in (
		"leftMetricsKey",
		"rightMetricsKey",
		"widthMetricsKey",
	):

		try:

			setattr(
				glyph,
				attribute,
				None,
			)

		except Exception:
			pass


def add_component(
	layer,
	componentName,
	x,
	scaleX=1.0,
	scaleY=1.0,
):

	component = GSComponent(
		componentName,
		NSPoint(
			x,
			0,
		),
	)

	try:

		component.automaticAlignment = False

	except Exception:
		pass

	try:

		component.scale = (
			scaleX,
			scaleY,
		)

	except Exception:

		try:

			component.transform = (
				(
					scaleX,
					0.0,
					0.0,
					scaleY,
					x,
					0.0,
				)
			)

		except Exception:
			pass

	shapes = list(
		layer.shapes
	)

	shapes.append(
		component
	)

	layer.shapes = shapes


def component_width(
	font,
	componentName,
	masterId,
):

	glyph = font.glyphs[
		componentName
	]

	if not glyph:
		return None

	try:

		layer = glyph.layers[
			masterId
		]

	except Exception:

		layer = None

	if not layer:
		return None

	return float(
		layer.width
	)


def ensure_glyph(
	font,
	name,
	source,
):

	glyph = font.glyphs[
		name
	]

	if glyph:

		return (
			glyph,
			False,
		)

	glyph = GSGlyph(
		name
	)

	font.glyphs.append(
		glyph
	)

	try:

		glyph.export = source.export

	except Exception:
		pass

	return (
		glyph,
		True,
	)


def glyph_has_master_content(
	font,
	glyph,
):

	if not glyph:
		return False

	for master in font.masters:

		try:

			layer = glyph.layers[
				master.id
			]

			if (
				layer
				and len(
					layer.shapes
				) > 0
			):

				return True

		except Exception:
			pass

	return False


def resolve_base_name(
	font,
	name,
	suffixes,
):

	if not name:
		return None

	for suffix in suffixes.values():

		if not name.endswith(
			suffix
		):

			continue

		base = name[
			:-len(suffix)
		]

		if font.glyphs[
			base
		]:

			return base

	return name


def selected_base_names(
	font,
	suffixes,
):

	selected = set()

	for layer in (
		font.selectedLayers
		or []
	):

		try:

			name = layer.parent.name

		except Exception:
			continue

		base = resolve_base_name(
			font,
			name,
			suffixes,
		)

		if (
			base
			and not base.startswith("_")
			and font.glyphs[base]
		):

			selected.add(
				base
			)

	return [
		glyph.name
		for glyph in font.glyphs
		if (
			glyph
			and glyph.name in selected
		)
	]


def eligible_base_names(
	font,
	suffixes,
):

	result = []

	allSuffixes = list(
		suffixes.values()
	)

	for glyph in font.glyphs:

		if (
			not glyph
			or not glyph.name
		):

			continue

		name = glyph.name

		if name == ".notdef":
			continue

		if name.startswith("_"):
			continue

		if any(
			name.endswith(suffix)
			for suffix in allSuffixes
		):
			continue

		try:

			if not glyph.export:
				continue

		except Exception:
			pass

		if not glyph_has_master_content(
			font,
			glyph,
		):

			continue

		result.append(
			name
		)

	return result


def listed_base_names(
	font,
	suffixes,
	text,
):

	requested = parse_glyph_list(
		text
	)

	bases = []
	missing = []
	unusable = []

	for name in requested:

		base = resolve_base_name(
			font,
			name,
			suffixes,
		)

		glyph = font.glyphs[
			base
		]

		if not glyph:

			missing.append(
				name
			)

			continue

		if base.startswith("_"):

			unusable.append(
				name
			)

			continue

		if not glyph_has_master_content(
			font,
			glyph,
		):

			unusable.append(
				name
			)

			continue

		if base not in bases:

			bases.append(
				base
			)

	ordered = [
		glyph.name
		for glyph in font.glyphs
		if (
			glyph
			and glyph.name in bases
		)
	]

	return (
		ordered,
		missing,
		unusable,
	)


def target_names(
	base,
	suffixes,
):

	return {
		"medi":
			base
			+ suffixes["medi"],

		"init":
			base
			+ suffixes["init"],

		"fina":
			base
			+ suffixes["fina"],

		"isol":
			base
			+ suffixes["isol"],
	}


def compact_names(
	names,
	limit=30,
):

	if len(names) <= limit:

		return " ".join(
			names
		)

	visible = names[
		:limit
	]

	return (
		" ".join(
			visible
		)
		+ f" … +{len(names) - limit}"
	)


# --------------------------------------------------------------------
# Builders
# --------------------------------------------------------------------

def build_medial(
	font,
	source,
	target,
	middleComponents,
	leftExtra,
	rightExtra,
	stretchMiddle,
):

	clear_glyph_metrics(
		target
	)

	for master in font.masters:

		try:

			sourceLayer = source.layers[
				master.id
			]

		except Exception:

			sourceLayer = None

		if not sourceLayer:

			raise ValueError(
				f"{source.name} has no layer "
				f"for master {master.name}."
			)

		targetLayer = get_master_layer(
			target,
			master.id,
		)

		reset_master_layer(
			targetLayer
		)

		medialWidth = (
			float(
				sourceLayer.width
			)
			+ leftExtra
			+ rightExtra
		)

		# --------------------------------------------------------
		# BACK
		# Middle streamer overlay(s).
		# --------------------------------------------------------

		for componentName in middleComponents:

			scaleX = 1.0

			if stretchMiddle:

				middleWidth = component_width(
					font,
					componentName,
					master.id,
				)

				if (
					middleWidth is None
					or abs(
						middleWidth
					) < 0.001
				):

					raise ValueError(
						f"{componentName} has zero width "
						f"in master {master.name} and "
						"cannot be stretched."
					)

				scaleX = (
					medialWidth
					/ middleWidth
				)

			add_component(
				targetLayer,
				componentName,
				0,
				scaleX,
				1.0,
			)

		# --------------------------------------------------------
		# FRONT
		# Default glyph shifts inward by added LSB.
		# --------------------------------------------------------

		add_component(
			targetLayer,
			source.name,
			leftExtra,
		)

		targetLayer.width = (
			medialWidth
		)


def build_sequence(
	font,
	target,
	sequence,
):

	clear_glyph_metrics(
		target
	)

	for master in font.masters:

		targetLayer = get_master_layer(
			target,
			master.id,
		)

		reset_master_layer(
			targetLayer
		)

		x = 0.0

		for componentName in sequence:

			width = component_width(
				font,
				componentName,
				master.id,
			)

			if width is None:

				raise ValueError(
					f"{componentName} has no layer "
					f"for master {master.name}."
				)

			add_component(
				targetLayer,
				componentName,
				x,
			)

			x += width

		targetLayer.width = x


# --------------------------------------------------------------------
# Interface
# --------------------------------------------------------------------

class StreamBuilderUI(object):

	def __init__(self):

		self.W = 540

		font = Glyphs.font

		self.componentItems = (
			component_suggestions(
				font
			)
		)

		self.w = Window(
			(
				self.W,
				760,
			),
			"Stream Builder",
		)

		y = 12

		# ------------------------------------------------------------
		# Positional Forms
		# ------------------------------------------------------------

		self.w.formsTitle = TextBox(
			(
				12,
				y,
				-12,
				16,
			),
			"POSITIONAL FORMS",
			sizeStyle="small",
		)

		y += 20

		self.w.isolLabel = TextBox(
			(
				12,
				y,
				150,
				18,
			),
			"Isolated suffix:",
			sizeStyle="small",
		)

		self.w.isolSuffixField = EditText(
			(
				162,
				y,
				-12,
				22,
			),
			".isol",
			sizeStyle="small",
		)

		y += 28

		self.w.initLabel = TextBox(
			(
				12,
				y,
				150,
				18,
			),
			"Initial suffix:",
			sizeStyle="small",
		)

		self.w.initSuffixField = EditText(
			(
				162,
				y,
				-12,
				22,
			),
			".init",
			sizeStyle="small",
		)

		y += 28

		self.w.mediLabel = TextBox(
			(
				12,
				y,
				150,
				18,
			),
			"Medial suffix:",
			sizeStyle="small",
		)

		self.w.mediSuffixField = EditText(
			(
				162,
				y,
				-12,
				22,
			),
			".medi",
			sizeStyle="small",
		)

		y += 28

		self.w.finaLabel = TextBox(
			(
				12,
				y,
				150,
				18,
			),
			"Final suffix:",
			sizeStyle="small",
		)

		self.w.finaSuffixField = EditText(
			(
				162,
				y,
				-12,
				22,
			),
			".fina",
			sizeStyle="small",
		)

		y += 30

		self.w.sep1 = HorizontalLine(
			(
				12,
				y,
				-12,
				1,
			)
		)

		y += 12

		# ------------------------------------------------------------
		# Stream Components
		# ------------------------------------------------------------

		self.w.partsTitle = TextBox(
			(
				12,
				y,
				-12,
				16,
			),
			"STREAM COMPONENTS",
			sizeStyle="small",
		)

		y += 17

		self.w.partsHint = TextBox(
			(
				12,
				y,
				-12,
				14,
			),
			"Suggests glyphs beginning with _; any valid glyph name can be entered manually.",
			sizeStyle="mini",
		)

		y += 20

		self.w.startLabel = TextBox(
			(
				12,
				y,
				150,
				18,
			),
			"Start:",
			sizeStyle="small",
		)

		self.w.startField = ComboBox(
			(
				162,
				y,
				-12,
				22,
			),
			self.componentItems,
			completes=True,
			sizeStyle="small",
		)

		y += 28

		self.w.middleLabel = TextBox(
			(
				12,
				y,
				150,
				18,
			),
			"Middle:",
			sizeStyle="small",
		)

		self.w.middleField = ComboBox(
			(
				162,
				y,
				-12,
				22,
			),
			self.componentItems,
			completes=True,
			sizeStyle="small",
		)

		y += 26

		self.w.stretchMiddle = CheckBox(
			(
				162,
				y,
				-12,
				20,
			),
			"Stretch middle to medial width",
			value=False,
			sizeStyle="small",
		)

		y += 26

		self.w.endLabel = TextBox(
			(
				12,
				y,
				150,
				18,
			),
			"End:",
			sizeStyle="small",
		)

		self.w.endField = ComboBox(
			(
				162,
				y,
				-12,
				22,
			),
			self.componentItems,
			completes=True,
			sizeStyle="small",
		)

		y += 30

		self.w.sep2 = HorizontalLine(
			(
				12,
				y,
				-12,
				1,
			)
		)

		y += 12

		# ------------------------------------------------------------
		# Spacing
		# ------------------------------------------------------------

		self.w.spacingTitle = TextBox(
			(
				12,
				y,
				-12,
				16,
			),
			"SPACING",
			sizeStyle="small",
		)

		y += 17

		self.w.spacingHint = TextBox(
			(
				12,
				y,
				-12,
				14,
			),
			"Adds space to the LSB and/or RSB of the default glyph.",
			sizeStyle="mini",
		)

		y += 20

		self.w.lsbLabel = TextBox(
			(
				12,
				y,
				150,
				18,
			),
			"Extra LSB:",
			sizeStyle="small",
		)

		self.w.lsbField = EditText(
			(
				162,
				y,
				70,
				22,
			),
			"25",
			sizeStyle="small",
		)

		y += 28

		self.w.rsbLabel = TextBox(
			(
				12,
				y,
				150,
				18,
			),
			"Extra RSB:",
			sizeStyle="small",
		)

		self.w.rsbField = EditText(
			(
				162,
				y,
				70,
				22,
			),
			"25",
			sizeStyle="small",
		)

		y += 30

		self.w.sep3 = HorizontalLine(
			(
				12,
				y,
				-12,
				1,
			)
		)

		y += 12

		# ------------------------------------------------------------
		# Build
		# ------------------------------------------------------------

		self.w.buildTitle = TextBox(
			(
				12,
				y,
				-12,
				16,
			),
			"BUILD",
			sizeStyle="small",
		)

		y += 20

		self.w.sourceLabel = TextBox(
			(
				12,
				y,
				150,
				18,
			),
			"Source:",
			sizeStyle="small",
		)

		self.w.sourcePopup = PopUpButton(
			(
				162,
				y,
				-12,
				22,
			),
			[
				"Selected glyphs",
				"All eligible glyphs",
				"Glyph list",
			],
			sizeStyle="small",
			callback=self.updateSourceInterface,
		)

		y += 28

		self.w.glyphListLabel = TextBox(
			(
				12,
				y,
				150,
				18,
			),
			"Glyph list:",
			sizeStyle="small",
		)

		self.w.glyphListField = EditText(
			(
				162,
				y,
				-12,
				22,
			),
			"",
			sizeStyle="small",
		)

		y += 28

		self.w.existingLabel = TextBox(
			(
				12,
				y,
				150,
				18,
			),
			"Existing forms:",
			sizeStyle="small",
		)

		self.w.existingPopup = PopUpButton(
			(
				162,
				y,
				-12,
				22,
			),
			[
				"Skip existing",
				"Rebuild existing",
			],
			sizeStyle="small",
		)

		y += 30

		self.w.sep4 = HorizontalLine(
			(
				12,
				y,
				-12,
				1,
			)
		)

		y += 12

		# ------------------------------------------------------------
		# Preview
		# ------------------------------------------------------------

		self.w.previewTitle = TextBox(
			(
				12,
				y,
				-12,
				16,
			),
			"PREVIEW",
			sizeStyle="small",
		)

		y += 20

		self.w.previewBox = TextEditor(
			(
				12,
				y,
				-12,
				150,
			),
			text=(
				"Choose a source and click Preview."
			),
		)

		try:

			ns = (
				self.w.previewBox
				.getNSTextView()
			)

			ns.setEditable_(
				False
			)

			ns.setSelectable_(
				True
			)

			ns.setDrawsBackground_(
				True
			)

			ns.setBackgroundColor_(
				NSColor.whiteColor()
			)

		except Exception:
			pass

		y += 162

		self.w.sep5 = HorizontalLine(
			(
				12,
				y,
				-12,
				1,
			)
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
			available
			/ 2
		)

		self.w.previewButton = Button(
			(
				left,
				y,
				btnW,
				btnH,
			),
			"Preview",
			callback=self.preview,
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

		x, yy, w, h = (
			self.w.getPosSize()
		)

		self.w.resize(
			w,
			y,
		)

		self.updateSourceInterface(
			None
		)

		self.w.open()


	# ------------------------------------------------------------
	# Dynamic UI
	# ------------------------------------------------------------

	def updateSourceInterface(
		self,
		sender,
	):

		useList = (
			self.w
			.sourcePopup
			.get()
			== 2
		)

		self.w.glyphListLabel.enable(
			useList
		)

		self.w.glyphListField.enable(
			useList
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

		return {
			"suffixes":
				suffixes,

			"start":
				parse_components(
					self.w
					.startField
					.get()
				),

			"middle":
				parse_components(
					self.w
					.middleField
					.get()
				),

			"end":
				parse_components(
					self.w
					.endField
					.get()
				),

			"stretch":
				bool(
					self.w
					.stretchMiddle
					.get()
				),

			"leftExtra":
				parse_number(
					self.w
					.lsbField
					.get(),
					0,
				),

			"rightExtra":
				parse_number(
					self.w
					.rsbField
					.get(),
					0,
				),

			"sourceMode":
				self.w
				.sourcePopup
				.get(),

			"glyphList":
				clean_string(
					self.w
					.glyphListField
					.get()
				),

			"rebuild":
				(
					self.w
					.existingPopup
					.get()
					== 1
				),
		}


	# ------------------------------------------------------------
	# Source
	# ------------------------------------------------------------

	def getSources(
		self,
		font,
		settings,
	):

		suffixes = settings[
			"suffixes"
		]

		mode = settings[
			"sourceMode"
		]

		if mode == 0:

			bases = selected_base_names(
				font,
				suffixes,
			)

			if not bases:

				return (
					None,
					"⚠️ Select one or more base glyphs first.",
				)

			return (
				bases,
				None,
			)

		if mode == 1:

			bases = eligible_base_names(
				font,
				suffixes,
			)

			if not bases:

				return (
					None,
					"⚠️ No eligible source glyphs found.",
				)

			return (
				bases,
				None,
			)

		if not settings[
			"glyphList"
		]:

			return (
				None,
				"⚠️ Enter one or more glyph names.",
			)

		(
			bases,
			missing,
			unusable,
		) = listed_base_names(
			font,
			suffixes,
			settings["glyphList"],
		)

		if missing:

			return (
				None,
				"⚠️ Glyph(s) not found: "
				+ ", ".join(
					missing
				),
			)

		if unusable:

			return (
				None,
				"⚠️ Glyph(s) cannot be used as sources: "
				+ ", ".join(
					unusable
				),
			)

		if not bases:

			return (
				None,
				"⚠️ No usable source glyphs found.",
			)

		return (
			bases,
			None,
		)


	# ------------------------------------------------------------
	# Analyze
	# ------------------------------------------------------------

	def analyze(self):

		font = Glyphs.font

		if not font:

			return (
				None,
				"⚠️ No font open.",
			)

		settings = self.settings()

		suffixes = settings[
			"suffixes"
		]

		if not all(
			suffixes.values()
		):

			return (
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
				"⚠️ The four positional suffixes must be different.",
			)

		allParts = (
			settings["start"]
			+ settings["middle"]
			+ settings["end"]
		)

		if not allParts:

			return (
				None,
				"⚠️ Enter at least one stream component.",
			)

		missingParts = [
			name
			for name in allParts
			if not font.glyphs[
				name
			]
		]

		if missingParts:

			return (
				None,
				"⚠️ Missing component glyph(s): "
				+ ", ".join(
					missingParts
				),
			)

		if (
			settings["stretch"]
			and not settings["middle"]
		):

			return (
				None,
				"⚠️ Add a middle component before enabling Stretch Middle.",
			)

		(
			bases,
			sourceError,
		) = self.getSources(
			font,
			settings,
		)

		if sourceError:

			return (
				None,
				sourceError,
			)

		if settings[
			"stretch"
		]:

			for componentName in settings[
				"middle"
			]:

				for master in font.masters:

					width = component_width(
						font,
						componentName,
						master.id,
					)

					if (
						width is None
						or abs(
							width
						) < 0.001
					):

						return (
							None,
							f"⚠️ {componentName} has zero width "
							f"in master {master.name} and "
							"cannot be stretched.",
						)

		generatedNames = set()

		for base in bases:

			for name in target_names(
				base,
				suffixes,
			).values():

				generatedNames.add(
					name
				)

		cycles = [
			name
			for name in allParts
			if name in generatedNames
		]

		if cycles:

			return (
				None,
				"⚠️ A stream component cannot also be one "
				"of the generated positional glyphs: "
				+ ", ".join(
					cycles
				),
			)

		return (
			{
				"font":
					font,

				"settings":
					settings,

				"bases":
					bases,
			},
			None,
		)


	# ------------------------------------------------------------
	# Report
	# ------------------------------------------------------------

	def report(
		self,
		data,
	):

		font = data[
			"font"
		]

		settings = data[
			"settings"
		]

		bases = data[
			"bases"
		]

		suffixes = settings[
			"suffixes"
		]

		lines = []

		lines.append(
			f"Source glyphs: {len(bases)}"
		)

		lines.append(
			"  "
			+ compact_names(
				bases
			)
		)

		lines.append("")

		lines.append(
			"Start: "
			+ (
				" + ".join(
					settings["start"]
				)
				if settings["start"]
				else "None"
			)
		)

		lines.append(
			"Middle: "
			+ (
				" + ".join(
					settings["middle"]
				)
				if settings["middle"]
				else "None"
			)
		)

		if settings[
			"middle"
		]:

			lines.append(
				"Middle stretch: "
				+ (
					"On"
					if settings["stretch"]
					else "Off"
				)
			)

		lines.append(
			"End: "
			+ (
				" + ".join(
					settings["end"]
				)
				if settings["end"]
				else "None"
			)
		)

		lines.append(
			"Medial spacing: "
			f"LSB {signed_number(settings['leftExtra'])} / "
			f"RSB {signed_number(settings['rightExtra'])}"
		)

		lines.append("")

		first = bases[
			0
		]

		names = target_names(
			first,
			suffixes,
		)

		mediRecipe = (
			settings["middle"]
			+ [first]
		)

		initRecipe = (
			settings["start"]
			+ [names["medi"]]
		)

		finaRecipe = (
			[names["medi"]]
			+ settings["end"]
		)

		isolRecipe = (
			settings["start"]
			+ [names["medi"]]
			+ settings["end"]
		)

		lines.append(
			"Example:"
		)

		lines.append(
			f"  {names['medi']} = "
			+ " + ".join(
				mediRecipe
			)
		)

		lines.append(
			f"  {names['init']} = "
			+ " + ".join(
				initRecipe
			)
		)

		lines.append(
			f"  {names['fina']} = "
			+ " + ".join(
				finaRecipe
			)
		)

		lines.append(
			f"  {names['isol']} = "
			+ " + ".join(
				isolRecipe
			)
		)

		existingCount = 0

		for base in bases:

			for name in target_names(
				base,
				suffixes,
			).values():

				glyph = font.glyphs[
					name
				]

				if glyph_has_master_content(
					font,
					glyph,
				):

					existingCount += 1

		if existingCount:

			lines.append("")

			if settings[
				"rebuild"
			]:

				lines.append(
					f"⚠️ {existingCount} existing form(s) "
					"will have their master layers rebuilt."
				)

			else:

				lines.append(
					f"{existingCount} populated existing form(s) "
					"will be skipped."
				)

		return "\n".join(
			lines
		)


	# ------------------------------------------------------------
	# Preview
	# ------------------------------------------------------------

	def preview(
		self,
		sender,
	):

		data, error = self.analyze()

		if error:

			self.w.previewBox.set(
				error
			)

			return

		self.w.previewBox.set(
			self.report(
				data
			)
		)


	# ------------------------------------------------------------
	# Run
	# ------------------------------------------------------------

	def run(
		self,
		sender,
	):

		data, error = self.analyze()

		if error:

			self.w.previewBox.set(
				error
			)

			return

		font = data[
			"font"
		]

		settings = data[
			"settings"
		]

		bases = data[
			"bases"
		]

		suffixes = settings[
			"suffixes"
		]

		created = 0
		rebuilt = 0
		skipped = 0

		font.disableUpdateInterface()

		try:

			for base in bases:

				source = font.glyphs[
					base
				]

				names = target_names(
					base,
					suffixes,
				)

				# Medial

				medi = font.glyphs[
					names["medi"]
				]

				if (
					medi
					and not settings["rebuild"]
					and glyph_has_master_content(
						font,
						medi,
					)
				):

					skipped += 1

				else:

					(
						medi,
						wasCreated,
					) = ensure_glyph(
						font,
						names["medi"],
						source,
					)

					build_medial(
						font,
						source,
						medi,
						settings["middle"],
						settings["leftExtra"],
						settings["rightExtra"],
						settings["stretch"],
					)

					if wasCreated:
						created += 1
					else:
						rebuilt += 1

				# Initial

				initGlyph = font.glyphs[
					names["init"]
				]

				if (
					initGlyph
					and not settings["rebuild"]
					and glyph_has_master_content(
						font,
						initGlyph,
					)
				):

					skipped += 1

				else:

					(
						initGlyph,
						wasCreated,
					) = ensure_glyph(
						font,
						names["init"],
						source,
					)

					build_sequence(
						font,
						initGlyph,
						settings["start"]
						+ [
							names["medi"]
						],
					)

					if wasCreated:
						created += 1
					else:
						rebuilt += 1

				# Final

				fina = font.glyphs[
					names["fina"]
				]

				if (
					fina
					and not settings["rebuild"]
					and glyph_has_master_content(
						font,
						fina,
					)
				):

					skipped += 1

				else:

					(
						fina,
						wasCreated,
					) = ensure_glyph(
						font,
						names["fina"],
						source,
					)

					build_sequence(
						font,
						fina,
						[
							names["medi"]
						]
						+ settings["end"],
					)

					if wasCreated:
						created += 1
					else:
						rebuilt += 1

				# Isolated

				isol = font.glyphs[
					names["isol"]
				]

				if (
					isol
					and not settings["rebuild"]
					and glyph_has_master_content(
						font,
						isol,
					)
				):

					skipped += 1

				else:

					(
						isol,
						wasCreated,
					) = ensure_glyph(
						font,
						names["isol"],
						source,
					)

					build_sequence(
						font,
						isol,
						settings["start"]
						+ [
							names["medi"]
						]
						+ settings["end"],
					)

					if wasCreated:
						created += 1
					else:
						rebuilt += 1

		except Exception as buildError:

			self.w.previewBox.set(
				"❌ Stream Builder stopped:\n\n"
				+ str(
					buildError
				)
			)

			print("")
			print(
				"❌ Stream Builder"
			)

			print(
				buildError
			)

			return

		finally:

			font.enableUpdateInterface()

			try:

				Glyphs.redraw()

			except Exception:
				pass

		report = self.report(
			data
		)

		report += (
			"\n\n"
			f"✅ Created: {created}"
			f" · Rebuilt: {rebuilt}"
			f" · Skipped: {skipped}"
		)

		self.w.previewBox.set(
			report
		)

		print("")
		print(
			"✔ Stream Builder"
		)

		print(
			f"→ Source glyphs: {len(bases)}"
		)

		print(
			f"→ Created: {created}"
		)

		print(
			f"→ Rebuilt: {rebuilt}"
		)

		print(
			f"→ Skipped: {skipped}"
		)

		print(
			"✅ Done."
		)


StreamBuilderUI()